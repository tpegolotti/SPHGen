#!/bin/bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: ./bench_sphgen.sh [args]
  -noavx512     Do not use AVX-512 version
  -noifma       Do not use AVX-512IFMA version
  -nokaratsuba  Do not run karatsuba multiplication
  -noopenssl    Do not run OpenSSL benchmarks
  -nohacl       Do not run HACL benchmarks
  -h, --help    Show this help text and exit
EOF
}

avx512_enabled=true
ifma_enabled=true
karatsuba_enabled=true
openssl_enabled=true
hacl_enabled=true
stride=1

# Parse long options manually
while (( "$#" )); do
  case "$1" in
    -noavx512)    avx512_enabled=false ;;
    -noifma)      ifma_enabled=false ;;
    -nokaratsuba) karatsuba_enabled=false ;;
    -noopenssl)   openssl_enabled=false ;;
    -nohacl)      hacl_enabled=false ;;
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
echo "OpenSSL benchmarks enabled: $openssl_enabled"
echo "HACL benchmarks enabled: $hacl_enabled"

DIR=poly1305_benchmarks
mkdir -p $DIR

if [ "$hacl_enabled" = true ]; then
    LD_LIBRARY_PATH=$(pwd)/others/hacl-star/dist/gcc-compatible:$LD_LIBRARY_PATH make bench_hacl | tee $DIR/hacl.csv
fi

if [ "$openssl_enabled" = true ]; then
    OPENSSL_ia32cap=0x0:0x20:0x0:0x0:0x0 make bench_openssl | tee $DIR/openssl_avx2.csv
    if [ "$avx512_enabled" = true ]; then
        OPENSSL_ia32cap=:~0x200000::: make bench_openssl | tee $DIR/openssl_avx512.csv
    fi
    if [ "$ifma_enabled" = true ]; then
        make bench_openssl | tee $DIR/openssl_avx512ifma.csv
    fi
fi



for unroll in 2 4 8
do
    make bench_one_inc UNROLL=$unroll SIMD=4 PI=130 THETA=5 | tee $DIR/poly1305_s4_u${unroll}.csv
done

if [ "$avx512_enabled" = true ]; then
    for unroll in 2 4 8
    do
        make bench_one_inc UNROLL=$unroll SIMD=8 PI=130 THETA=5 | tee $DIR/poly1305_s8_u${unroll}.csv
    done
fi

if [ "$karatsuba_enabled" = true ]; then
    for unroll in 2 4 8
    do
        make bench_one_inc UNROLL=$unroll SIMD=4 PI=130 THETA=5 KARA=-k | tee $DIR/poly1305_s4_u${unroll}_kara.csv
    done
    if [ "$avx512_enabled" = true ]; then
        for unroll in 2 4 8
        do
            make bench_one_inc UNROLL=$unroll SIMD=8 PI=130 THETA=5 KARA=-k | tee $DIR/poly1305_s8_u${unroll}_kara.csv
        done
    fi
fi


if [ "$ifma_enabled" = true ]; then
    for unroll in 2 4 8
    do
        make bench_one_inc UNROLL=$unroll SIMD=8 PI=130 THETA=5 MADD=--madd| tee $DIR/poly1305_s8_ifma_u${unroll}.csv
    done
fi
