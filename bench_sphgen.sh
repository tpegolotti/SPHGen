#!/bin/bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: ./bench_sphgen.sh [args]
  -noavx512     Do not use AVX-512 version
  -noifma       Do not use AVX-512IFMA version
  -nokaratsuba  Do not run karatsuba multiplication
  -stride N     Process every N-th test case (default: 1)
  -h, --help    Show this help text and exit
EOF
}

avx512_enabled=true
ifma_enabled=true
karatsuba_enabled=true
stride=1

# Parse long options manually
while (( "$#" )); do
  case "$1" in
    -noavx512)    avx512_enabled=false ;;
    -noifma)      ifma_enabled=false ;;
    -nokaratsuba) karatsuba_enabled=false ;;
    -stride)      stride="$2"; shift ;;
    -h|--help)    show_help; exit 0 ;;
    --)           shift; break ;;          # end of options
    -*)           printf 'Unknown option: %s\n' "$1" >&2; show_help; exit 1 ;;
    *)            break ;;                 # first non-option argument
  esac
  shift
done

echo "AVX-512 enabled: $avx512_enabled"
echo "AVX-512IFMA enabled: $ifma_enabled"
echo "Karatsuba multiplication enabled: $karatsuba_enabled"
echo "Stride: $stride"

DIR=sphgen_benchmarks
mkdir -p $DIR


if [ "$ifma_enabled" = true ]; then
    for unroll in 1 4 8
    do
        make plot STRIDE=$stride UNROLL=$unroll SIMD=8 MADD=--madd | tee $DIR/s8_ifma_u${unroll}.csv
    done
fi

if [ "$avx512_enabled" = true ]; then
    for unroll in 1 4 8
    do
        make plot STRIDE=$stride UNROLL=$unroll SIMD=8 | tee $DIR/s8_u${unroll}.csv
    done
fi

for unroll in 1 4 8
do
    make plot STRIDE=$stride UNROLL=$unroll SIMD=4 | tee $DIR/s4_u${unroll}.csv
done

if [ "$karatsuba_enabled" = true ]; then
    if [ "$avx512_enabled" = true ]; then
        for unroll in 1 4 8
        do
            make plot STRIDE=$stride UNROLL=$unroll SIMD=8 KARA=--karatsuba | tee $DIR/s8_u${unroll}_kara.csv
        done
    fi
    for unroll in 1 4 8
    do
        make plot STRIDE=$stride UNROLL=$unroll SIMD=4 KARA=--karatsuba | tee $DIR/s4_u${unroll}_kara.csv
    done
fi