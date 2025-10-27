# SPHGen: A Program Generator for Fast Polynomial Hash Functions

## Dependencies

Generating the library requires Jinja for template generation, sympy and numpy for verification. Running `pip install -r requirements.txt` installs the packages.

### Optional dependencies

To run experiments from the paper, the following dependencies are needed.

We use NTL (Number Theoretic Library) for testing the correctness of the output. We follow the instructions from the [installation guide](https://libntl.org/doc/tour-unix.html). 

```
# starting from the root of the project
apt-get install  libgmp3-dev                # needed for NTL
wget https://libntl.org/ntl-11.5.1.tar.gz   # the version we used
gunzip ntl-11.5.1.tar.gz 
tar xf ntl-11.5.1.tar 
mv ntl-11.5.1 ntl                           # renaming the folder, needed for the makefile to find the library
cd ntl/src/
./configure 
make -j
make check # optional
sudo make install
```

SPHGen can be used to generate a polynomial hash function for any given Crandall Prime Field. This includes the classical poly1305 hash function. We compare against OpenSSL and HACL for that case.

Example setup:
```
# starting from the root of the project
cd others
git clone https://github.com/openssl/openssl
cd openssl/
./Configure 
make -j
cd ..

# starting from others/
git clone https://github.com/hacl-star/hacl-star
cd hacl-star/dist/gcc-compatible/
make -j
```

### Jasmin

SPHGen supports generating both C and [Jasmin](https://github.com/jasmin-lang/jasmin) code. Jasmin code can then either used for verification, or can be compiled to assembly. We install Jasmin using `opam install jasmin`, but other possibilities are available [here](https://github.com/jasmin-lang/jasmin/wiki/Installation-instructions).



## Generating the library

There are a few options:
  - `make main` creates a binary that benchmarks and tests one specific prime version
  - `make test` creates a binary that tests one specific prime
  - `make plot` benchmarks for various prime fields

Makefile options:
  - `PI`: sets up the power of 2 for the prime
  - `THETA`: sets up the factor to subtract from 2^PI
  - `UNROLL`: maximum factor to unroll the innermost loop
  - `SIMD`: decides between AVX2 and AVX512. Options=4,8.
  - `MADD`: activates AVX512_IFMA. Options=--madd,-m. Requires SIMD=8.
  - `KARA`: activates Karatsuba multiplication. Options=--karatsuba,-k

## Benchmarking OpenSSL and HACL*
We give in `./others` the scripts using to benchmark OpenSSL and HACL*. They require installing the libraries in the same directory. See the above setup. We give commands to run benchmarks for increasing size of messages:
  - `make bench_hacl` benchmarks hacl*. Requires `export LD_LIBRARY_PATH=$(pwd)/others/hacl-star/dist/gcc-compatible:$LD_LIBRARY_PATH`
  - `make bench_openssl` benchmarks openssl


