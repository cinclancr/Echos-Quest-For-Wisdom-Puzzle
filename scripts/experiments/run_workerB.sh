#!/bin/bash
# worker B: Electrum-validity permutation scans (3 top sets), then joins
# the full no-checksum scan of the midpoint set on blocks 5..10.
cd /home/z/my-project/Echos-Quest-For-Wisdom-Puzzle
B=scripts/experiments/nochecksum_scan
ALL=0,1,2,3,4,5,6,7,8,9,10
$B electrum1 data/english.txt results/scan/words_dset.txt      results/scan/elc_dset      $ALL 0 >> results/scan/elc_dset.log 2>&1
$B electrum1 data/english.txt results/scan/words_p5_nonext.txt results/scan/elc_p5nonext  $ALL 0 >> results/scan/elc_p5nonext.log 2>&1
$B electrum1 data/english.txt results/scan/words_p5_nohint.txt results/scan/elc_p5nohint $ALL 0 >> results/scan/elc_p5nohint.log 2>&1
$B full      data/english.txt results/scan/words_dset.txt      results/scan/ncs 5,6,7,8,9,10 0 >> results/scan/ncs_wB.log 2>&1
