#!/bin/bash
# Reruns after the soak (02:42): the jobs that crashed with VAE tiles of 1024, now with 512, under the GPU lock.
N=$(dirname "$0"); C=/home/annejan/Projects/music/code; PY="$C/.venv/bin/python -W ignore"; L=$N/gpu.lock
cd $C
sleep 30                                   # queue 2's first job holds the lock by now
for s in warm_boot:warm-boot_120bpm_Am.wav low_pass_love:low-pass-love_122bpm_Am.wav; do
  song=${s%%:*}; wav=${s#*:}
  echo "$(date +%T) polish sft $song"
  flock $L $PY produce.py $song --project projects/_polish_sft.toml --tag nm-sft65 --ours renders/$wav > $N/jobs/rerun_polish_$song.log 2>&1
  echo "$(date +%T) exit $?"
done
flock $L true                              # wait for the first vocals job to end
if [ ! -f renders/ace/packet_loss/vocals-sft-0.95-s1.wav ] || grep -q DeviceLost renders/ace/packet_loss/vocals-sft-0.95-s1.synth.log; then
  echo "$(date +%T) vocals sft 0.95 packet_loss again"
  flock $L $PY ace.py packet_loss --mode vocals --model sft --strength 0.95 > $N/jobs/rerun_vocals_packet_loss.log 2>&1
  echo "$(date +%T) exit $?"
fi
$PY $N/polish_ab.py > $N/jobs/rerun_polish_ab.log 2>&1; echo "$(date +%T) polish A-B again: exit $?"
