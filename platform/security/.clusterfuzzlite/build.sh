#!/bin/bash -eu

cd "$SRC/ordivon-security-v2"
pip3 install .

for fuzzer in "$SRC"/ordivon-security-v2/fuzz/*_fuzzer.py; do
  fuzzer_basename=$(basename -s .py "$fuzzer")
  fuzzer_package=${fuzzer_basename}.pkg
  pyinstaller --distpath "$OUT" --onefile --name "$fuzzer_package" "$fuzzer"
  cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
# LLVMFuzzerTestOneInput for ClusterFuzzLite fuzzer detection.
this_dir=\$(dirname "\$0")
exec "\$this_dir/$fuzzer_package" "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
