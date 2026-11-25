/*
 * nochecksum_scan.c — full-permutation BIP39/Electrum address scanner
 * =====================================================================
 *
 * Motivation: BIP39 seed derivation (PBKDF2-HMAC-SHA512 over the mnemonic
 * string) does NOT depend on the checksum. A puzzle author can hand-pick
 * twelve words from a story and still derive a perfectly standard wallet
 * with a checksum-invalid mnemonic.  All earlier scanning in this project
 * gated address derivation on BIP39 checksum validity (1/16 of the space);
 * this tool removes that gate.
 *
 * Modes
 * -----
 *   selftest  — built-in BIP39/Electrum known-answer vectors + golden file
 *   full      — every permutation of (first word + 11 unknowns) is derived
 *               with the BIP39 KDF (salt "mnemonic") at the selected paths
 *               and compared against the puzzle target hash160.  NO
 *               checksum gate; checksum validity is counted for audit only.
 *   electrum  — every permutation is checked against the Electrum 2.x
 *               "new seed" version tag: HMAC-SHA512("Seed version", phrase)
 *               beginning with byte 0x01 (standard wallet).  Survivors
 *               (~1/256 of permutations) are derived with the Electrum KDF
 *               (salt "electrum") at Electrum standard paths m/0/i, m/1/j
 *               AND with the BIP39 KDF at standard paths.
 *
 * Enumeration order matches Python itertools.permutations(unknowns) exactly
 * (lexicographic order of position tuples), so checkpoints and results are
 * directly comparable with the Python tools in this repository.  The 11!
 * space is split into 11 contiguous "blocks" (first-word position 0..10);
 * a worker scans a comma list of blocks.
 *
 * Checkpointing: per-block state files are written atomically (tmp+rename);
 * an interrupted run resumes at its exact block offset.
 *
 * Safety: read-only research tool.  A match is recorded as word indices plus
 * derivation parameters only — never raw key material.  No network access.
 *
 * Build:  gcc -O2 -o nochecksum_scan nochecksum_scan.c -lcrypto
 *         (add -Wno-deprecated-declarations to silence OpenSSL 3 hints)
 */

#define _POSIX_C_SOURCE 200809L
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/sha.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

/* ---------------------------------------------------------------- constants */

static const char *TARGET_ADDRESS = "1GABd5r3dYTYqSoRcErghjZTbV6zJXZJBx";
static void reference_target(void) { (void)TARGET_ADDRESS; }
/* hash160 of the target address, version 0x00 */
static const unsigned char TARGET_H160[20] = {
    0xa6, 0x46, 0x7f, 0x50, 0x64, 0x42, 0xff, 0x57, 0x66, 0xbd,
    0x31, 0x35, 0x15, 0x90, 0x1d, 0x92, 0x92, 0xc8, 0x4e, 0x53};

static const uint64_t FACT10 = 3628800ULL; /* 10! permutations per block */

/* ------------------------------------------------------------- crypto state */

static EC_GROUP *GRP = NULL;
static BN_CTX *BCTX = NULL;
static const BIGNUM *ORDER = NULL; /* secp256k1 group order (borrowed) */
static BIGNUM *BN_K = NULL;       /* current private key scalar */
static BIGNUM *BN_IL = NULL;      /* current HMAC tweak */
static BIGNUM *BN_T = NULL;       /* temp */
static EC_POINT *P = NULL;

static void ec_init(void)
{
    GRP = EC_GROUP_new_by_curve_name(NID_secp256k1);
    BCTX = BN_CTX_new();
    ORDER = EC_GROUP_get0_order(GRP);
    BN_K = BN_new();
    BN_IL = BN_new();
    BN_T = BN_new();
    P = EC_POINT_new(GRP);
}

static void sha256(const void *d, size_t n, unsigned char out[32])
{
    EVP_Digest(d, n, out, NULL, EVP_sha256(), NULL);
}

static void ripemd160(const void *d, size_t n, unsigned char out[20])
{
    EVP_Digest(d, n, out, NULL, EVP_ripemd160(), NULL);
}

static void hmac_sha512(const void *key, size_t keylen,
                        const void *data, size_t datalen,
                        unsigned char out[64])
{
    unsigned int olen = 0;
    HMAC(EVP_sha512(), key, (int)keylen, data, datalen, out, &olen);
}

static void pbkdf2_fast(const char *pass, size_t plen,
                        const unsigned char *salt, size_t slen,
                        unsigned char out[64]);

static void pbkdf2_sha512(const char *pass, size_t passlen,
                          const unsigned char *salt, size_t saltlen,
                          unsigned char out[64])
{
    pbkdf2_fast(pass, passlen, salt, saltlen, out);
}

/* ===================================================== fast secp256k1 (local)
 * 4x64-bit little-endian limbs in the Montgomery domain (R = 2^256 mod p).
 * Only what the scan needs: scalar*G with a precomputed table of 2^i*G
 * (table built once from OpenSSL, which keeps the hand-written surface
 * small); point formula is the EFD madd-2007-bl mixed addition (Z2 = 1).
 * The selftest differentially validates this code against OpenSSL for
 * many deterministic scalars and both public-key encodings.
 */

typedef uint64_t fe[4];

static const uint64_t MODP[4] = {0xFFFFFFFEFFFFFC2FULL, 0xFFFFFFFFFFFFFFFFULL,
                                  0xFFFFFFFFFFFFFFFFULL, 0xFFFFFFFFFFFFFFFFULL};
static const uint64_t NP_C = 0xD838091DD2253531ULL; /* -p^-1 mod 2^64 */
static const fe FE_R2 = {0x7A2000E90A1ULL, 0x1ULL, 0, 0}; /* R^2 mod p */
static const fe FE_ONE_R = {0x1000003D1ULL, 0, 0, 0};    /* R mod p = Mont(1) */
static const fe FE_ONE = {1, 0, 0, 0};

static void fe_mul(fe o, const fe a, const fe b)
{
    /* 9-limb accumulator: the delayed-shift REDC intermediate can exceed
     * 2^512 (ninth limb = the q >= 2^256 case), handled with a second
     * conditional subtraction.  Fuzz-validated against Python. */
    uint64_t t[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
    for (int i = 0; i < 4; i++)
    {
        uint64_t carry = 0;
        for (int j = 0; j < 4; j++)
        {
            unsigned __int128 s = (unsigned __int128)a[i] * b[j] + t[i + j] + carry;
            t[i + j] = (uint64_t)s;
            carry = (uint64_t)(s >> 64);
        }
        t[i + 4] = carry;
    }
    for (int i = 0; i < 4; i++)
    {
        uint64_t m = t[i] * NP_C;
        uint64_t carry = 0;
        for (int j = 0; j < 4; j++)
        {
            unsigned __int128 s = (unsigned __int128)m * MODP[j] + t[i + j] + carry;
            t[i + j] = (uint64_t)s;
            carry = (uint64_t)(s >> 64);
        }
        for (int k = i + 4; carry && k < 9; k++)
        {
            unsigned __int128 s = (unsigned __int128)t[k] + carry;
            t[k] = (uint64_t)s;
            carry = (uint64_t)(s >> 64);
        }
    }
    if (t[8] == 0)
    {
        /* q = t[4..7] < 2p: one conditional subtraction */
        int ge = 0;
        for (int i = 3; i >= 0; i--)
        {
            if (t[4 + i] > MODP[i]) { ge = 1; break; }
            if (t[4 + i] < MODP[i]) break;
        }
        if (ge)
        {
            uint64_t borrow = 0;
            for (int i = 0; i < 4; i++)
            {
                unsigned __int128 s = (unsigned __int128)t[4 + i] - MODP[i] - borrow;
                t[4 + i] = (uint64_t)s;
                borrow = (uint64_t)((int64_t)(s >> 64) & 1);
            }
        }
    }
    else
    {
        /* q = t[4..7] + 2^256 > p: subtract p, then conditional subtract */
        uint64_t borrow = 0;
        for (int i = 0; i < 4; i++)
        {
            unsigned __int128 s = (unsigned __int128)t[4 + i] - MODP[i] - borrow;
            t[4 + i] = (uint64_t)s;
            borrow = (uint64_t)((int64_t)(s >> 64) & 1);
        }
        int ge = 0;
        for (int i = 3; i >= 0; i--)
        {
            if (t[4 + i] > MODP[i]) { ge = 1; break; }
            if (t[4 + i] < MODP[i]) break;
        }
        if (ge)
        {
            uint64_t borrow2 = 0;
            for (int i = 0; i < 4; i++)
            {
                unsigned __int128 s = (unsigned __int128)t[4 + i] - MODP[i] - borrow2;
                t[4 + i] = (uint64_t)s;
                borrow2 = (uint64_t)((int64_t)(s >> 64) & 1);
            }
        }
    }
    o[0] = t[4]; o[1] = t[5]; o[2] = t[6]; o[3] = t[7];
}

static void fe_sqr(fe o, const fe a) { fe_mul(o, a, a); }

static void fe_add(fe o, const fe a, const fe b)
{
    uint64_t carry = 0;
    for (int i = 0; i < 4; i++)
    {
        unsigned __int128 s = (unsigned __int128)a[i] + b[i] + carry;
        o[i] = (uint64_t)s;
        carry = (uint64_t)(s >> 64);
    }
    if (carry)
    {
        /* subtract p once (2^256 > p) */
        uint64_t borrow = 0;
        for (int i = 0; i < 4; i++)
        {
            unsigned __int128 s = (unsigned __int128)o[i] - MODP[i] - borrow;
            o[i] = (uint64_t)s;
            borrow = (uint64_t)((int64_t)(s >> 64) & 1);
        }
    }
    else
    {
        int ge = 0;
        for (int i = 3; i >= 0; i--)
        {
            if (o[i] > MODP[i]) { ge = 1; break; }
            if (o[i] < MODP[i]) break;
        }
        if (ge)
        {
            uint64_t borrow = 0;
            for (int i = 0; i < 4; i++)
            {
                unsigned __int128 s = (unsigned __int128)o[i] - MODP[i] - borrow;
                o[i] = (uint64_t)s;
                borrow = (uint64_t)((int64_t)(s >> 64) & 1);
            }
        }
    }
}

static void fe_sub(fe o, const fe a, const fe b)
{
    uint64_t borrow = 0;
    for (int i = 0; i < 4; i++)
    {
        unsigned __int128 s = (unsigned __int128)a[i] - b[i] - borrow;
        o[i] = (uint64_t)s;
        borrow = (uint64_t)((int64_t)(s >> 64) & 1);
    }
    if (borrow)
    {
        uint64_t carry = 0;
        for (int i = 0; i < 4; i++)
        {
            unsigned __int128 s = (unsigned __int128)o[i] + MODP[i] + carry;
            o[i] = (uint64_t)s;
            carry = (uint64_t)(s >> 64);
        }
    }
}

static void fe_dbl(fe o, const fe a) { fe_add(o, a, a); }

/* plain 32-byte big-endian -> Montgomery */
static void fe_from_bytes(fe o, const unsigned char b[32])
{
    for (int i = 0; i < 4; i++)
        o[i] = ((uint64_t)b[24 - 8 * i] << 56) | ((uint64_t)b[25 - 8 * i] << 48) |
               ((uint64_t)b[26 - 8 * i] << 40) | ((uint64_t)b[27 - 8 * i] << 32) |
               ((uint64_t)b[28 - 8 * i] << 24) | ((uint64_t)b[29 - 8 * i] << 16) |
               ((uint64_t)b[30 - 8 * i] << 8) | (uint64_t)b[31 - 8 * i];
    fe tmp;
    fe_mul(tmp, o, FE_R2);
    o[0] = tmp[0]; o[1] = tmp[1]; o[2] = tmp[2]; o[3] = tmp[3];
}

/* Montgomery -> plain 32-byte big-endian */
static void fe_to_bytes(unsigned char b[32], const fe a)
{
    fe t;
    fe_mul(t, a, FE_ONE);
    for (int i = 0; i < 4; i++)
    {
        b[24 - 8 * i] = (unsigned char)(t[i] >> 56);
        b[25 - 8 * i] = (unsigned char)(t[i] >> 48);
        b[26 - 8 * i] = (unsigned char)(t[i] >> 40);
        b[27 - 8 * i] = (unsigned char)(t[i] >> 32);
        b[28 - 8 * i] = (unsigned char)(t[i] >> 24);
        b[29 - 8 * i] = (unsigned char)(t[i] >> 16);
        b[30 - 8 * i] = (unsigned char)(t[i] >> 8);
        b[31 - 8 * i] = (unsigned char)(t[i]);
    }
}

/* a^(p-2) mod p via fixed-exponent binary ladder (Montgomery domain in/out) */
static void fe_inv(fe o, const fe a)
{
    static const unsigned char pm2[32] = {
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFE, 0xFF, 0xFF, 0xFC, 0x2D};
    fe r = {FE_ONE_R[0], FE_ONE_R[1], FE_ONE_R[2], FE_ONE_R[3]};
    fe base;
    base[0] = a[0]; base[1] = a[1]; base[2] = a[2]; base[3] = a[3];
    for (int i = 255; i >= 0; i--)
    {
        fe_sqr(r, r);
        if ((pm2[31 - i / 8] >> (i & 7)) & 1)
            fe_mul(r, r, base);
    }
    o[0] = r[0]; o[1] = r[1]; o[2] = r[2]; o[3] = r[3];
}

/* Jacobian point; Z == 0 encodes infinity */
typedef struct { fe x, y, z; } jac;

static fe GTX[256], GTY[256]; /* affine Montgomery, 2^i * G */

static void gtable_init(void)
{
    BIGNUM *e = BN_new();
    unsigned char buf[65];
    for (int i = 0; i < 256; i++)
    {
        BN_set_word(e, 0);
        BN_set_bit(e, i);
        EC_POINT_mul(GRP, P, e, NULL, NULL, BCTX);
        EC_POINT_point2oct(GRP, P, POINT_CONVERSION_UNCOMPRESSED, buf, 65, BCTX);
        fe_from_bytes(GTX[i], buf + 1);
        fe_from_bytes(GTY[i], buf + 33);
    }
    BN_free(e);
}

/* mixed addition acc += affine (X2,Y2), derived and numerically verified:
 *   U2 = X2*Z1^2 ; S2 = Y2*Z1^3 ; H = U2-X1 ; R = S2-Y1
 *   X3 = R^2 - H^3 - 2*X1*H^2
 *   Y3 = R*(X1*H^2 - X3) - Y1*H^3
 *   Z3 = Z1*H
 * (H==0 only if acc == table point, impossible for distinct 2^i*G sums) */
static void j_madd(jac *acc, const fe X2, const fe Y2)
{
    if (acc->z[0] == 0 && acc->z[1] == 0 && acc->z[2] == 0 && acc->z[3] == 0)
    {
        for (int i = 0; i < 4; i++)
        {
            acc->x[i] = X2[i];
            acc->y[i] = Y2[i];
            acc->z[i] = FE_ONE_R[i];
        }
        return;
    }
    fe z1z1, u2, s2, h, r, h2, h3, x3, y3, z3, t, t2;
    fe_sqr(z1z1, acc->z);            /* Z1^2 */
    fe_mul(u2, X2, z1z1);            /* U2 = X2*Z1^2 */
    fe_mul(t, acc->z, z1z1);         /* Z1^3 */
    fe_mul(s2, Y2, t);               /* S2 = Y2*Z1^3 */
    fe_sub(h, u2, acc->x);           /* H = U2 - X1 */
    fe_sub(r, s2, acc->y);           /* R = S2 - Y1 */
    fe_sqr(h2, h);                   /* H^2 */
    fe_mul(h3, h, h2);               /* H^3 */
    /* X3 = R^2 - H^3 - 2*X1*H^2 */
    fe_sqr(x3, r);
    fe_sub(x3, x3, h3);
    fe_mul(t2, acc->x, h2);
    fe_dbl(t2, t2);
    fe_sub(x3, x3, t2);
    /* Y3 = R*(X1*H^2 - X3) - Y1*H^3 */
    fe_mul(t2, acc->x, h2);          /* X1*H^2 */
    fe_sub(t2, t2, x3);              /* X1*H^2 - X3 */
    fe_mul(y3, r, t2);
    fe_mul(t2, acc->y, h3);          /* Y1*H^3 */
    fe_sub(y3, y3, t2);
    /* Z3 = Z1*H */
    fe_mul(z3, acc->z, h);
    for (int i = 0; i < 4; i++)
    {
        acc->x[i] = x3[i];
        acc->y[i] = y3[i];
        acc->z[i] = z3[i];
    }
}

/* scalar * G -> compressed pub (33B) and uncompressed (65B) in one pass.
 * kb is 32-byte big-endian; returns 0 for zero scalar. */
static int fast_pub(const unsigned char kb[32], unsigned char comp[33], unsigned char uncomp[65])
{
    jac acc;
    memset(&acc, 0, sizeof acc);
    for (int i = 255; i >= 0; i--)
    {
        if ((kb[31 - i / 8] >> (i & 7)) & 1)
            j_madd(&acc, GTX[i], GTY[i]);
    }
    if (acc.z[0] == 0 && acc.z[1] == 0 && acc.z[2] == 0 && acc.z[3] == 0)
        return 0;
    fe zi, zi2, zi3, xa, ya;
    fe_inv(zi, acc.z);
    fe_sqr(zi2, zi);
    fe_mul(zi3, zi2, zi);
    fe_mul(xa, acc.x, zi2);
    fe_mul(ya, acc.y, zi3);
    unsigned char xb[32], yb[32];
    fe_to_bytes(xb, xa);
    fe_to_bytes(yb, ya);
    uncomp[0] = 0x04;
    memcpy(uncomp + 1, xb, 32);
    memcpy(uncomp + 33, yb, 32);
    comp[0] = (unsigned char)(0x02 | (yb[31] & 1));
    memcpy(comp + 1, xb, 32);
    return 1;
}

/* --------------------------------------------------- fast PBKDF2-SHA512 (2048)
 * The mnemonic string is < 112 bytes and the salt < 108 bytes, so both HMAC
 * key pads and all messages fit single SHA-512 blocks: each PBKDF2 round is
 * exactly two compressions from cached ipad/opad midstates. */

static void pbkdf2_fast(const char *pass, size_t plen,
                        const unsigned char *salt, size_t slen,
                        unsigned char out[64])
{
    if (plen > 111 || slen + 4 > 111)
    {
        PKCS5_PBKDF2_HMAC(pass, (int)plen, salt, (int)slen, 2048, EVP_sha512(), 64, out);
        return;
    }
    unsigned char ipad[128], opad[128];
    memset(ipad, 0x36, 128);
    memset(opad, 0x5C, 128);
    for (size_t i = 0; i < plen; i++)
    {
        ipad[i] ^= (unsigned char)pass[i];
        opad[i] ^= (unsigned char)pass[i];
    }
    SHA512_CTX ictx, octx, c;
    SHA512_Init(&ictx);
    SHA512_Update(&ictx, ipad, 128);
    SHA512_Init(&octx);
    SHA512_Update(&octx, opad, 128);
    unsigned char U[64], T[64], inner[64], cnt[4] = {0, 0, 0, 1};
    c = ictx;
    SHA512_Update(&c, salt, slen);
    SHA512_Update(&c, cnt, 4);
    SHA512_Final(inner, &c);
    c = octx;
    SHA512_Update(&c, inner, 64);
    SHA512_Final(U, &c);
    memcpy(T, U, 64);
    for (int it = 1; it < 2048; it++)
    {
        c = ictx;
        SHA512_Update(&c, U, 64);
        SHA512_Final(inner, &c);
        c = octx;
        SHA512_Update(&c, inner, 64);
        SHA512_Final(U, &c);
        for (int b = 0; b < 64; b++)
            T[b] ^= U[b];
    }
    memcpy(out, T, 64);
}

/* ------------------------------------------------------------ BIP32 helpers */

static unsigned char CHAIN_CUR[32];

static int ckd_apply(const unsigned char *data, size_t datalen)
{
    unsigned char digest[64];
    hmac_sha512(CHAIN_CUR, 32, data, datalen, digest);
    BN_bin2bn(digest, 32, BN_IL);
    if (BN_cmp(BN_IL, ORDER) >= 0)
        return 0; /* invalid tweak — astronomically rare for a scan */
    if (!BN_mod_add(BN_T, BN_K, BN_IL, ORDER, BCTX))
        return 0;
    if (BN_is_zero(BN_T))
        return 0;
    BN_copy(BN_K, BN_T);
    memcpy(CHAIN_CUR, digest + 32, 32);
    return 1;
}

static int ckd_hardened(uint32_t index)
{
    unsigned char data[1 + 32 + 4];
    data[0] = 0;
    BN_bn2binpad(BN_K, data + 1, 32);
    data[33] = (unsigned char)(index >> 24);
    data[34] = (unsigned char)(index >> 16);
    data[35] = (unsigned char)(index >> 8);
    data[36] = (unsigned char)(index);
    return ckd_apply(data, 37);
}

static int ckd_normal(uint32_t index)
{
    unsigned char pub[33], uncomp[65], kb[32];
    unsigned char data[33 + 4];
    BN_bn2binpad(BN_K, kb, 32);
    if (!fast_pub(kb, pub, uncomp))
        return 0;
    memcpy(data, pub, 33);
    data[33] = (unsigned char)(index >> 24);
    data[34] = (unsigned char)(index >> 16);
    data[35] = (unsigned char)(index >> 8);
    data[36] = (unsigned char)(index);
    return ckd_apply(data, 37);
}

/* ---------------------------------------------------------------- path list */

enum path_id
{
    PATH_PRIMARY = 0, /* m/44'/0'/0'/0/0 */
    PATH_M0_0,        /* m/0/0 */
    PATH_M0_1,        /* m/0/1 */
    PATH_M0_2,        /* m/0/2 */
    PATH_M0_3,        /* m/0/3 */
    PATH_M0_4,        /* m/0/4 */
    PATH_M1_0,        /* m/1/0 */
    PATH_M1_1,        /* m/1/1 */
    PATH_M00P,        /* m/0'/0/0 */
    PATH_M,           /* m  (root) */
    PATH_COUNT
};

static const char *PATH_NAMES[PATH_COUNT] = {
    "m/44'/0'/0'/0/0", "m/0/0", "m/0/1", "m/0/2", "m/0/3", "m/0/4",
    "m/1/0", "m/1/1", "m/0'/0/0", "m"};

/* Derive the address key at a path from a seed.  Result key in BN_K. */
static int derive_path(const unsigned char seed[64], enum path_id pid)
{
    unsigned char digest[64];
    hmac_sha512("Bitcoin seed", 12, seed, 64, digest);
    BN_bin2bn(digest, 32, BN_K);
    memcpy(CHAIN_CUR, digest + 32, 32);
    if (BN_is_zero(BN_K) || BN_cmp(BN_K, ORDER) >= 0)
        return 0;
    switch (pid)
    {
    case PATH_PRIMARY:
        return ckd_hardened(0x8000002Cu) && ckd_hardened(0x80000000u) &&
               ckd_hardened(0x80000000u) && ckd_normal(0) && ckd_normal(0);
    case PATH_M0_0:
    case PATH_M0_1:
    case PATH_M0_2:
    case PATH_M0_3:
    case PATH_M0_4:
        return ckd_normal(0) && ckd_normal((uint32_t)(pid - PATH_M0_0));
    case PATH_M1_0:
    case PATH_M1_1:
        return ckd_normal(1) && ckd_normal((uint32_t)(pid - PATH_M1_0));
    case PATH_M00P:
        return ckd_hardened(0x80000000u) && ckd_normal(0) && ckd_normal(0);
    case PATH_M:
        return 1;
    default:
        return 0;
    }
}

/* address test: point of current key k (BIGNUM), both encodings via fast EC */
static int key_matches_target(BIGNUM *k, int *comp_hit, int *uncomp_hit)
{
    unsigned char comp[33], uncomp[65], sha[32], rip[20], kb[32];
    int hit = 0;
    *comp_hit = *uncomp_hit = 0;
    BN_bn2binpad(k, kb, 32);
    if (!fast_pub(kb, comp, uncomp))
        return 0;
    sha256(comp, 33, sha);
    ripemd160(sha, 32, rip);
    if (memcmp(rip, TARGET_H160, 20) == 0)
        *comp_hit = 1, hit = 1;
    sha256(uncomp, 65, sha);
    ripemd160(sha, 32, rip);
    if (memcmp(rip, TARGET_H160, 20) == 0)
        *uncomp_hit = 1, hit = 1;
    return hit;
}

/* ---------------------------------------------------------------- utilities */

static void utc_now(char *buf, size_t n)
{
    time_t t = time(NULL);
    struct tm tmv;
    gmtime_r(&t, &tmv);
    strftime(buf, n, "%Y-%m-%dT%H:%M:%SZ", &tmv);
}

/* lexicographic next permutation over arr[0..n-1] */
static int next_perm(int *arr, int n)
{
    int i = n - 2;
    while (i >= 0 && arr[i] >= arr[i + 1])
        i--;
    if (i < 0)
        return 0;
    int j = n - 1;
    while (arr[j] <= arr[i])
        j--;
    int tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
    for (int a = i + 1, b = n - 1; a < b; a++, b--)
    {
        tmp = arr[a];
        arr[a] = arr[b];
        arr[b] = tmp;
    }
    return 1;
}

/* ---------------------------------------------------------------- word data */

static char WL[2048][16];
static int WLEN[2048];
static int WIDX[12]; /* 0-based BIP39 indices of the 12 words (first pinned) */

static int load_wordlist(const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f)
        return -1;
    char line[64];
    int n = 0;
    {
        reference_target(); /* keep the human-readable target pinned for docs */
    }
    while (n < 2048 && fgets(line, sizeof line, f))
    {
        char *nl = strpbrk(line, "\r\n");
        if (nl)
            *nl = 0;
        if (line[0] == 0)
            continue;
        size_t ll = strlen(line);
        if (ll > 15)
            ll = 15; /* BIP39 words are <= 8 chars; defensive bound */
        memcpy(WL[n], line, ll);
        WL[n][ll] = 0;
        WLEN[n] = (int)ll;
        n++;
    }
    fclose(f);
    return n == 2048 ? 0 : -1;
}

static int wl_find(const char *w)
{
    for (int i = 0; i < 2048; i++)
        if (strcmp(WL[i], w) == 0)
            return i;
    return -1;
}

static int build_phrase(const int *widx, char *buf, size_t bufsz)
{
    /* fast path: 12 known words, memcpy join (order is all that varies) */
    size_t off = 0;
    for (int i = 0; i < 12; i++)
    {
        if (i)
            buf[off++] = ' ';
        size_t len = (size_t)WLEN[widx[i]];
        if (off + len + 1 >= bufsz)
            return -1;
        memcpy(buf + off, WL[widx[i]], len);
        off += len;
    }
    buf[off] = 0;
    return (int)off;
}

/* BIP39 checksum validity for 12 word indices */
static int bip39_checksum_valid(const int widx[12])
{
    unsigned char ent[16], sha[32];
    unsigned __int128 acc = 0;
    int have = 0;
    for (int i = 0; i < 12; i++)
    {
        unsigned v = (unsigned)widx[i];
        if (i < 11)
        {
            acc = (acc << 11) | v;
            have += 11;
        }
        else
        {
            acc = (acc << 7) | (v >> 4);
            have += 7;
        }
    }
    (void)have; /* 128 bits */
    for (int b = 15; b >= 0; b--)
    {
        ent[b] = (unsigned char)(acc & 0xFF);
        acc >>= 8;
    }
    sha256(ent, 16, sha);
    return (sha[0] >> 4) == (widx[11] & 0xF);
}

/* Electrum 2.x "new seed" standard version tag: first byte 0x01.
 * Fast variant with precomputed HMAC-SHA512 ipad/opad midstates
 * (key "Seed version" is fixed). */
static SHA512_CTX SV_ICTX, SV_OCTX;

static void seed_version_init(void)
{
    unsigned char key[128];
    memset(key, 0, 128);
    memcpy(key, "Seed version", 12);
    unsigned char pad[128];
    for (int i = 0; i < 128; i++)
        pad[i] = key[i] ^ 0x36;
    SHA512_Init(&SV_ICTX);
    SHA512_Update(&SV_ICTX, pad, 128);
    for (int i = 0; i < 128; i++)
        pad[i] = key[i] ^ 0x5c;
    SHA512_Init(&SV_OCTX);
    SHA512_Update(&SV_OCTX, pad, 128);
}

static int electrum_valid(const char *phrase, size_t len)
{
    SHA512_CTX c;
    unsigned char d[64];
    if (len > 111) /* phrase + padding must fit a single block */
    {
        unsigned char digest[64];
        hmac_sha512("Seed version", 12, phrase, len, digest);
        return digest[0] == 0x01;
    }
    c = SV_ICTX;
    SHA512_Update(&c, phrase, len);
    SHA512_Final(d, &c);
    c = SV_OCTX;
    SHA512_Update(&c, d, 64);
    SHA512_Final(d, &c);
    return d[0] == 0x01;
}

/* ------------------------------------------------------------ match records */

static char STATE_PREFIX[512];

static void write_match(const char *mode, const int widx[12], int path_id,
                        int compressed, const char *kdf)
{
    char ts[40];
    utc_now(ts, sizeof ts);
    char path[640];
    snprintf(path, sizeof path, "%s.match", STATE_PREFIX);
    FILE *f = fopen(path, "a");
    if (!f)
        return;
    fprintf(f, "{\"mode\":\"%s\",\"word_indices\":[", mode);
    for (int i = 0; i < 12; i++)
        fprintf(f, "%d%s", widx[i], i == 11 ? "" : ",");
    fprintf(f, "],\"path\":\"%s\",\"compressed\":%s,\"kdf\":\"%s\",\"found_utc\":\"%s\"}\n",
            PATH_NAMES[path_id], compressed ? "true" : "false", kdf, ts);
    fclose(f);
    fprintf(stderr, "!!! MATCH: mode=%s path=%s kdf=%s compressed=%d indices=[",
            mode, PATH_NAMES[path_id], kdf, compressed);
    for (int i = 0; i < 12; i++)
        fprintf(stderr, "%d ", widx[i]);
    fprintf(stderr, "]\n");
}

/* ---------------------------------------------------------------- scan core */

typedef struct
{
    char phrase[512];
    unsigned char seed[64];
    int pos[11];
    uint64_t block;
    uint64_t offset;
    uint64_t processed;
    uint64_t checksum_valid;
    uint64_t electrum_valid;
    uint64_t derived;
    uint64_t matches;
} scan_ctx;

static void save_block_state(scan_ctx *c, const char *mode, double elapsed, int complete)
{
    char tmp[640], path[640];
    snprintf(tmp, sizeof tmp, "%s.state.b%d.tmp", STATE_PREFIX, (int)c->block);
    FILE *f = fopen(tmp, "w");
    if (!f)
        return;
    fprintf(f,
            "{\"mode\":\"%s\",\"block\":%llu,\"offset\":%llu,"
            "\"processed\":%llu,\"checksum_valid\":%llu,"
            "\"electrum_valid\":%llu,\"derived\":%llu,\"matches\":%llu,"
            "\"elapsed_s\":%.1f,\"complete\":%s}\n",
            mode, (unsigned long long)c->block, (unsigned long long)c->offset,
            (unsigned long long)c->processed, (unsigned long long)c->checksum_valid,
            (unsigned long long)c->electrum_valid, (unsigned long long)c->derived,
            (unsigned long long)c->matches, elapsed, complete ? "true" : "false");
    fclose(f);
    snprintf(path, sizeof path, "%s.state.b%d", STATE_PREFIX, (int)c->block);
    rename(tmp, path);
}

static void log_progress(scan_ctx *c, double rate)
{
    char path[640], ts[40];
    utc_now(ts, sizeof ts);
    snprintf(path, sizeof path, "%s.progress", STATE_PREFIX);
    FILE *f = fopen(path, "a");
    if (!f)
        return;
    fprintf(f,
            "{\"utc\":\"%s\",\"block\":%llu,\"offset\":%llu,\"processed\":%llu,"
            "\"checksum_valid\":%llu,\"electrum_valid\":%llu,\"derived\":%llu,"
            "\"matches\":%llu,\"rate_per_s\":%.1f}\n",
            ts, (unsigned long long)c->block, (unsigned long long)c->offset,
            (unsigned long long)c->processed, (unsigned long long)c->checksum_valid,
            (unsigned long long)c->electrum_valid, (unsigned long long)c->derived,
            (unsigned long long)c->matches, rate);
    fclose(f);
}

/* derive & compare one mnemonic at the enabled paths for the given mode */
static void test_permutation(scan_ctx *c, const int widx[12], const char *mode,
                             const char *passphrase)
{
    int plen = build_phrase(widx, c->phrase, sizeof c->phrase);
    if (plen < 0)
        return;
    c->derived++;
    if (bip39_checksum_valid(widx))
        c->checksum_valid++;

    unsigned char salt[160];
    int sl;
    enum path_id epaths[] = {PATH_M0_0, PATH_M0_1, PATH_M0_2, PATH_M0_3,
                             PATH_M0_4, PATH_M1_0, PATH_M1_1};
    enum path_id bpaths[] = {PATH_PRIMARY, PATH_M00P, PATH_M0_0};

    if (strcmp(mode, "full") == 0)
    {
        sl = snprintf((char *)salt, sizeof salt, "mnemonic%s", passphrase);
        pbkdf2_sha512(c->phrase, (size_t)plen, salt, (size_t)sl, c->seed);
        {
            if (derive_path(c->seed, PATH_PRIMARY))
            {
                int ch, uh;
                if (key_matches_target(BN_K, &ch, &uh))
                {
                    c->matches++;
                    write_match("full", widx, PATH_PRIMARY, ch, "bip39");
                    if (uh && !ch)
                        write_match("full", widx, PATH_PRIMARY, 0, "bip39");
                }
            }
        }
    }
    else if (strcmp(mode, "electrum1") == 0)
    {
        if (!electrum_valid(c->phrase, (size_t)plen))
            return;
        c->electrum_valid++;
        sl = snprintf((char *)salt, sizeof salt, "electrum%s", passphrase);
        pbkdf2_sha512(c->phrase, (size_t)plen, salt, (size_t)sl, c->seed);
        if (derive_path(c->seed, PATH_M0_0))
        {
            int ch, uh;
            if (key_matches_target(BN_K, &ch, &uh))
            {
                c->matches++;
                write_match("electrum1", widx, PATH_M0_0, ch, "electrum");
                if (uh && !ch)
                    write_match("electrum1", widx, PATH_M0_0, 0, "electrum");
            }
        }
    }
    else if (strcmp(mode, "electrum") == 0)
    {
        if (!electrum_valid(c->phrase, (size_t)plen))
            return;
        c->electrum_valid++;
        /* Electrum KDF at Electrum standard-wallet paths */
        sl = snprintf((char *)salt, sizeof salt, "electrum%s", passphrase);
        pbkdf2_sha512(c->phrase, (size_t)plen, salt, (size_t)sl, c->seed);
        for (unsigned p = 0; p < sizeof epaths / sizeof epaths[0]; p++)
        {
            if (derive_path(c->seed, epaths[p]))
            {
                int ch, uh;
                if (key_matches_target(BN_K, &ch, &uh))
                {
                    c->matches++;
                    write_match("electrum", widx, epaths[p], ch, "electrum");
                    if (uh && !ch)
                        write_match("electrum", widx, epaths[p], 0, "electrum");
                }
            }
        }
        /* same Electrum-valid phrase imported as BIP39 */
        sl = snprintf((char *)salt, sizeof salt, "mnemonic%s", passphrase);
        pbkdf2_sha512(c->phrase, (size_t)plen, salt, (size_t)sl, c->seed);
        for (unsigned p = 0; p < sizeof bpaths / sizeof bpaths[0]; p++)
        {
            if (derive_path(c->seed, bpaths[p]))
            {
                int ch, uh;
                if (key_matches_target(BN_K, &ch, &uh))
                {
                    c->matches++;
                    write_match("electrum", widx, bpaths[p], ch, "bip39");
                    if (uh && !ch)
                        write_match("electrum", widx, bpaths[p], 0, "bip39");
                }
            }
        }
    }
}

/* scan one block starting at start_offset; returns when block done or
 * budget seconds elapsed (<=0 means unlimited) */
static void run_block(scan_ctx *c, uint64_t block, uint64_t start_offset,
                      const char *mode, const char *passphrase, double budget)
{
    c->block = block;
    c->offset = start_offset;
    int remaining[11], rc = 0;
    for (int i = 0; i <= 10; i++)
        if (i != (int)block)
            remaining[rc++] = i;
    c->pos[0] = (int)block;
    for (int i = 0; i < 10; i++)
        c->pos[1 + i] = remaining[i];

    uint64_t skip = start_offset;
    while (skip-- > 0 && next_perm(c->pos + 1, 10))
        ;

    struct timespec t0, now;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t since_ckpt = 0, since_log = 0;
    int widx[12];
    widx[0] = WIDX[0];

    for (;;)
    {
        for (int i = 0; i < 11; i++)
            widx[1 + i] = WIDX[1 + c->pos[i]];
        test_permutation(c, widx, mode, passphrase);
        c->processed++;
        c->offset++;
        since_ckpt++;
        since_log++;
        if (!next_perm(c->pos + 1, 10))
            break;
        if (since_ckpt >= 250000)
        {
            clock_gettime(CLOCK_MONOTONIC, &now);
            double el = (now.tv_sec - t0.tv_sec) + (now.tv_nsec - t0.tv_nsec) / 1e9;
            save_block_state(c, mode, el, 0);
            since_ckpt = 0;
        }
        if (since_log >= 1000000)
        {
            clock_gettime(CLOCK_MONOTONIC, &now);
            double el = (now.tv_sec - t0.tv_sec) + (now.tv_nsec - t0.tv_nsec) / 1e9;
            log_progress(c, c->processed / (el + 1e-9));
            since_log = 0;
        }
        if (budget > 0 && (c->processed & 0xFFF) == 0)
        {
            clock_gettime(CLOCK_MONOTONIC, &now);
            double el = (now.tv_sec - t0.tv_sec) + (now.tv_nsec - t0.tv_nsec) / 1e9;
            if (el > budget)
                break;
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &now);
    double el = (now.tv_sec - t0.tv_sec) + (now.tv_nsec - t0.tv_nsec) / 1e9;
    int complete = c->offset >= FACT10;
    save_block_state(c, mode, el, complete);
}

/* ------------------------------------------------------------------ selftest */

static int h160_of_key(const char *mnemonic, const char *salt_word,
                       enum path_id pid, char hex_out[41])
{
    unsigned char seed[64], pub[33], sha[32], rip[20];
    unsigned char salt[80];
    int sl = snprintf((char *)salt, sizeof salt, "%s", salt_word);
    pbkdf2_sha512(mnemonic, strlen(mnemonic), salt, (size_t)sl, seed);
    if (!derive_path(seed, pid))
        return 0;
    if (!EC_POINT_mul(GRP, P, BN_K, NULL, NULL, BCTX))
        return 0;
    if (EC_POINT_point2oct(GRP, P, POINT_CONVERSION_COMPRESSED, pub, 33, BCTX) != 33)
        return 0;
    sha256(pub, 33, sha);
    ripemd160(sha, 32, rip);
    for (int i = 0; i < 20; i++)
        sprintf(hex_out + 2 * i, "%02x", rip[i]);
    return 1;
}

static int selftest(const char *golden_path)
{
    int ok = 1;
    unsigned char seed[64], rip[20];
    char hex[129], h41[41];

    /* 1. BIP39 official vector (Trezor vectors.json[0]) */
    const char *mn = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
    pbkdf2_sha512(mn, strlen(mn), (const unsigned char *)"mnemonicTREZOR", 14, seed);
    const char *want = "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04";
    for (int i = 0; i < 64; i++)
        sprintf(hex + 2 * i, "%02x", seed[i]);
    printf("selftest pbkdf2 bip39 vector: %s\n", strcmp(hex, want) == 0 ? "OK" : "FAIL");
    ok &= strcmp(hex, want) == 0;

    /* 2. RIPEMD-160 known answer */
    ripemd160("abc", 3, rip);
    int rip_ok = memcmp(rip, "\x8e\xb2\x08\xf7\xe0\x5d\x98\x7a\x9b\x04\x4a\x8e\x98\xc6\xb0\x87\xf1\x5a\x0b\xfc", 20) == 0;
    printf("selftest ripemd160(abc): %s\n", rip_ok ? "OK" : "FAIL");
    ok &= rip_ok;

    /* 3. Electrum KDF + m/0/0 golden (Python-generated, wordlist cross-check) */
    const char *phrase = "echo more vivid night like maze fury renew hint they what upon";
    if (h160_of_key(phrase, "electrum", PATH_M0_0, h41))
    {
        int e_ok = strcmp(h41, "8562910dd3471ff656df9ada42bfeb2e407eb4b8") == 0;
        printf("selftest electrum m/0/0 h160: %s\n", e_ok ? "OK" : "FAIL");
        ok &= e_ok;
    }
    else
    {
        printf("selftest electrum m/0/0: derive FAILED\n");
        ok = 0;
    }

    /* 4. golden permutations file: lines "mnemonic\th160_primary\th160_m00" */
    if (golden_path && strcmp(golden_path, "-") != 0)
    {
        FILE *f = fopen(golden_path, "r");
        if (!f)
        {
            printf("selftest golden file not readable: %s\n", golden_path);
            return ok;
        }
        char line[512];
        int checked = 0, passed = 0;
        while (fgets(line, sizeof line, f))
        {
            char *t1 = strchr(line, '\t');
            if (!t1)
                continue;
            *t1 = 0;
            char *t2 = strchr(t1 + 1, '\t');
            if (!t2)
                continue;
            *t2 = 0;
            char *end = strpbrk(t2 + 1, "\r\n");
            if (end)
                *end = 0;
            if (h160_of_key(line, "mnemonic", PATH_PRIMARY, h41))
            {
                checked++;
                if (strcmp(h41, t1 + 1) == 0)
                    passed++;
            }
            if (h160_of_key(line, "mnemonic", PATH_M0_0, h41))
            {
                checked++;
                if (strcmp(h41, t2 + 1) == 0)
                    passed++;
            }
        }
        fclose(f);
        printf("selftest golden permutations: %d/%d passed\n", passed, checked);
        ok &= (checked > 0 && passed == checked);
    }

    /* 5. differential test: fast secp256k1 vs OpenSSL for deterministic
     * scalars (LCG), both public key encodings. */
    {
        BIGNUM *kk = BN_new();
        unsigned char comp[33], uncomp[65], osslcomp[33], ossluncomp[65], kb[32];
        int n_ok = 0, n_tot = 0;
        uint64_t lcg = 88172645463325252ULL;
        for (int t = 0; t < 128; t++)
        {
            lcg = lcg * 6364136223846793005ULL + 1442695040888963407ULL;
            unsigned char raw[32];
            for (int b = 0; b < 32; b += 8)
            {
                memcpy(raw + b, &lcg, 8);
                lcg = lcg * 6364136223846793005ULL + 1442695040888963407ULL;
            }
            BN_bin2bn(raw, 32, kk);
            if (BN_is_zero(kk) || BN_cmp(kk, ORDER) >= 0)
                continue;
            BN_bn2binpad(kk, kb, 32);
            if (!fast_pub(kb, comp, uncomp))
                continue;
            EC_POINT_mul(GRP, P, kk, NULL, NULL, BCTX);
            EC_POINT_point2oct(GRP, P, POINT_CONVERSION_COMPRESSED, osslcomp, 33, BCTX);
            EC_POINT_point2oct(GRP, P, POINT_CONVERSION_UNCOMPRESSED, ossluncomp, 65, BCTX);
            n_tot++;
            if (memcmp(comp, osslcomp, 33) == 0 && memcmp(uncomp, ossluncomp, 65) == 0)
                n_ok++;
        }
        /* also the exact generator and a couple of known small multiples */
        BN_set_word(kk, 1);
        BN_bn2binpad(kk, kb, 32);
        if (fast_pub(kb, comp, uncomp))
        {
            EC_POINT_mul(GRP, P, kk, NULL, NULL, BCTX);
            EC_POINT_point2oct(GRP, P, POINT_CONVERSION_COMPRESSED, osslcomp, 33, BCTX);
            n_tot += 2;
            if (comp[0] == 0x02) n_ok++; /* G has even y */
            if (memcmp(comp + 1,
                       "\x79\xBE\x66\x7E\xF9\xDC\xBB\xAC\x55\xA0\x62\x95\xCE\x87\x0B\x07"
                       "\x02\x9B\xFC\xDB\x2D\xCE\x28\xD9\x59\xF2\x81\x5B\x16\xF8\x17\x98", 32) == 0)
                n_ok++;
        }
        BN_free(kk);
        printf("selftest fast-ec vs openssl: %d/%d matches\n", n_ok, n_tot);
        /* count n_ok < n_tot would indicate mismatch; require full match of
         * the 128 random ones plus the G checks */
        ok &= (n_ok == n_tot);
    }

    printf("selftest result: %s\n", ok ? "ALL OK" : "FAILURES PRESENT");
    return ok;
}

/* ------------------------------------------------------------ derive mode */
/* Deterministic cross-validation harness: reads a file of 12-word
 * phrases (one per line), derives the BIP39 seed (salt "mnemonic" +
 * optional passphrase) and prints, for EVERY path the scanner can test,
 * the compressed AND uncompressed hash160 of the derived key:
 *   <vecid> <path> <comp_h160> <uncomp_h160> <checksum_valid>
 * Any derivation or pubkey failure prints a FAIL line and flips the exit
 * status — errors are never silently counted as negative results. */

static void hex20(const unsigned char *rip, char out[41])
{
    for (int i = 0; i < 20; i++)
        sprintf(out + 2 * i, "%02x", rip[i]);
}

static int derive_one(int vecid, const char *phrase, int plen,
                       const char *passphrase, int checksum_valid)
{
    unsigned char salt[160], seed[64], comp[33], uncomp[65], sha[32], rip[20], kb[32];
    int sl = snprintf((char *)salt, sizeof salt, "mnemonic%s", passphrase);
    pbkdf2_sha512(phrase, (size_t)plen, salt, (size_t)sl, seed);
    const enum path_id paths[] = {PATH_PRIMARY, PATH_M00P, PATH_M0_0, PATH_M0_1,
                                  PATH_M0_2, PATH_M0_3, PATH_M0_4, PATH_M1_0, PATH_M1_1};
    const char *names[] = {"m/44'/0'/0'/0/0", "m/0'/0/0", "m/0/0", "m/0/1",
                            "m/0/2", "m/0/3", "m/0/4", "m/1/0", "m/1/1"};
    int fails = 0;
    for (unsigned p = 0; p < sizeof paths / sizeof paths[0]; p++)
    {
        if (!derive_path(seed, paths[p]))
        {
            printf("%d %s DERIVE-FAIL\n", vecid, names[p]);
            fails++;
            continue;
        }
        BN_bn2binpad(BN_K, kb, 32);
        if (!fast_pub(kb, comp, uncomp))
        {
            printf("%d %s PUBKEY-FAIL\n", vecid, names[p]);
            fails++;
            continue;
        }
        char hc[41], hu[41];
        sha256(comp, 33, sha);
        ripemd160(sha, 32, rip);
        hex20(rip, hc);
        sha256(uncomp, 65, sha);
        ripemd160(sha, 32, rip);
        hex20(rip, hu);
        printf("%d %s %s %s %d\n", vecid, names[p], hc, hu, checksum_valid);
    }
    return fails;
}

static int derive_mode(const char *wlpath, const char *vecfile, const char *passphrase)
{
    if (load_wordlist(wlpath) != 0)
    {
        fprintf(stderr, "wordlist must contain 2048 entries: %s\n", wlpath);
        return 2;
    }
    FILE *f = fopen(vecfile, "r");
    if (!f)
    {
        fprintf(stderr, "cannot read vectors file %s\n", vecfile);
        return 2;
    }
    char line[512];
    int vecid = 0, fails = 0, lines_bad = 0;
    while (fgets(line, sizeof line, f))
    {
        char *nl = strpbrk(line, "\r\n");
        if (nl)
            *nl = 0;
        char phrase[512];
        size_t off = 0;
        int widx[12], n = 0, bad = 0;
        char *tok = strtok(line, " \t");
        phrase[0] = 0;
        while (tok)
        {
            if (n >= 12)
            {
                bad = 1;
                break;
            }
            int idx = wl_find(tok);
            if (idx < 0)
            {
                bad = 1;
                break;
            }
            widx[n++] = idx;
            size_t tl = strlen(tok);
            if (off + tl + 2 >= sizeof phrase)
            {
                bad = 1;
                break;
            }
            if (off)
                phrase[off++] = ' ';
            memcpy(phrase + off, tok, tl);
            off += tl;
            phrase[off] = 0;
            tok = strtok(NULL, " \t");
        }
        if (bad || n != 12)
        {
            fprintf(stderr, "vector %d: malformed line (12 BIP39 words required)\n", vecid);
            lines_bad++;
            fails++;
            vecid++;
            continue;
        }
        fails += derive_one(vecid, phrase, (int)off, passphrase,
                            bip39_checksum_valid(widx));
        vecid++;
    }
    fclose(f);
    fprintf(stderr, "derive: %d vectors, %d hard failures, %d malformed lines\n",
            vecid, fails, lines_bad);
    if (vecid == 0)
        return 2;
    return fails ? 1 : 0;
}

/* --------------------------------------------------------------------- main */

static void usage(const char *argv0)
{
    fprintf(stderr,
            "usage: %s <mode> <wordlist> <wordsfile> <stateprefix> <blocks|all> <budget_seconds|0> [passphrase|-] [goldenfile|-]\n"
            "  mode: selftest | full | electrum | electrum1 | derive\n"
            "  wordsfile: 12 lines; line 1 is the pinned first word (echo)\n"
            "  blocks: comma list of 0..10 first-word positions for this worker (or all)\n"
            "  derive mode (cross-validation): %s derive <wordlist> <vectorsfile> [passphrase|-]\n"
            "    vectorsfile: one 12-word phrase per line; prints per-phrase, per-path\n"
            "    hash160 (compressed + uncompressed) TSV to stdout\n",
            argv0, argv0);
    exit(2);
}

int main(int argc, char **argv)
{
    if (argc < 2)
        usage(argv[0]);
    const char *mode = argv[1];

    ec_init();
    seed_version_init();
    gtable_init();

    /* derive mode: cross-validation harness, argument shape differs */
    if (strcmp(mode, "derive") == 0)
    {
        if (argc < 4)
            usage(argv[0]);
        const char *pass = (argc > 4 && strcmp(argv[4], "-") != 0) ? argv[4] : "";
        return derive_mode(argv[2], argv[3], pass);
    }

    if (argc < 7)
        usage(argv[0]);
    const char *wlpath = argv[2];
    const char *wordsfile = argv[3];
    const char *prefix = argv[4];
    const char *blockspec = argv[5];
    double budget = atof(argv[6]);
    const char *passphrase = (argc > 7 && strcmp(argv[7], "-") != 0) ? argv[7] : "";
    const char *golden = (argc > 8 && strcmp(argv[8], "-") != 0) ? argv[8] : "-";

    if (strcmp(mode, "selftest") == 0)
        return selftest(golden) ? 0 : 1;

    if (load_wordlist(wlpath) != 0)
    {
        fprintf(stderr, "wordlist must contain 2048 entries: %s\n", wlpath);
        return 2;
    }

    /* load candidate words (12 lines) */
    {
        FILE *f = fopen(wordsfile, "r");
        if (!f)
        {
            fprintf(stderr, "cannot read words file %s\n", wordsfile);
            return 2;
        }
        char line[64];
        int n = 0;
        while (n < 12 && fgets(line, sizeof line, f))
        {
            char *nl = strpbrk(line, "\r\n");
            if (nl)
                *nl = 0;
            if (line[0] == 0)
                continue;
            char word[32];
            strncpy(word, line, 31);
            word[31] = 0;
            int idx = wl_find(word);
            if (idx < 0)
            {
                fprintf(stderr, "word not in BIP39 wordlist: '%s'\n", word);
                return 2;
            }
            WIDX[n] = idx;
            n++;
        }
        fclose(f);
        if (n != 12)
        {
            fprintf(stderr, "words file must have 12 words, got %d\n", n);
            return 2;
        }
    }

    strncpy(STATE_PREFIX, prefix, sizeof STATE_PREFIX - 1);

    scan_ctx ctx;
    memset(&ctx, 0, sizeof ctx);

    int blocks[16], nblocks = 0;
    if (strcmp(blockspec, "all") == 0)
    {
        for (int i = 0; i < 11; i++)
            blocks[nblocks++] = i;
    }
    else
    {
        char *spec = strdup(blockspec);
        for (char *tok = strtok(spec, ","); tok && nblocks < 16; tok = strtok(NULL, ","))
            blocks[nblocks++] = atoi(tok);
        free(spec);
    }
    if (nblocks == 0)
        usage(argv[0]);

    for (int b = 0; b < nblocks; b++)
    {
        uint64_t start_offset = 0;
        char path[640];
        snprintf(path, sizeof path, "%s.state.b%d", STATE_PREFIX, blocks[b]);
        FILE *f = fopen(path, "r");
        if (f)
        {
            char buf[512];
            if (fgets(buf, sizeof buf, f))
            {
                char *o = strstr(buf, "\"offset\":");
                if (o)
                    start_offset = strtoull(o + 9, NULL, 10);
                char *cm = strstr(buf, "\"complete\":true");
                if (cm && start_offset >= FACT10)
                {
                    fclose(f);
                    fprintf(stderr, "block %d already complete\n", blocks[b]);
                    continue;
                }
            }
            fclose(f);
        }
        ctx.block = 0;
        ctx.processed = 0;
        ctx.checksum_valid = 0;
        ctx.electrum_valid = 0;
        ctx.derived = 0;
        ctx.matches = 0;
        run_block(&ctx, (uint64_t)blocks[b], start_offset, mode, passphrase, budget);
        fprintf(stderr, "worker block %d: offset=%llu checksum_valid=%llu electrum_valid=%llu derived=%llu matches=%llu\n",
                blocks[b], (unsigned long long)ctx.offset,
                (unsigned long long)ctx.checksum_valid,
                (unsigned long long)ctx.electrum_valid,
                (unsigned long long)ctx.derived,
                (unsigned long long)ctx.matches);
    }
    return 0;
}
