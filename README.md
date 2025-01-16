# SPHGen: A Program Generator for Fast Polynomial Hash Functions

## Dependencies

- NTL (number theoretic library) to check correctness of algorithm ([Installation guide](https://libntl.org/doc/tour-unix.html)). Place NTL library in a `./ntl` directory to run tests.
- Jinja2 for template generation (`pip install -r requirements.txt`)

## Generating the library

There are a few options:
  - `make main` creates a binary that benchmarks and tests one specific prime version
  - `make test` creates a binary that tests one specific prime
  - `make plot` benchmarks for various prime fields

Makefile options:
  - `PI`: sets up the power of 2 for the prime
  - `THETA`: sets up the factor to subtract from 2^PI
  - `UNROLL`: maximum factor to unroll the innermost loop (I usually set it up to around 4 otherwise for some primes it takes a lot to compile)
  - `SIMD`: decides between AVX2 and AVX512. Options=4,8.
  - `MADD`: activates AVX512_IFMA. Options=--madd,-m. Requires SIMD=8.
  - `KARA`: activates Karatsuba multiplication. Options=--karatsuba,-k

## Benchmarking OpenSSL and HACL*
We give in `./others` the scripts using to benchmark OpenSSL and HACL*. They require installing the libraries in the same directory. We give commands to run benchmarks for increasing size of messages:
  - `make bench_hacl` benchmarks hacl*
  - `make bench_openssl` benchmarks openssl