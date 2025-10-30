# SPHGen: A Program Generator for Fast Polynomial Hash Functions

Code for the paper "SPHGen: A Program Generator for Fast Polynomial Hash Functions" submitted at the Conference on Cryptographic Hardware and Embedded Systems (CHES) 2026. Given a Crandall Prime of the form $2^\pi - \theta$, SPHGen generates a vectorized polynomial hash function for that prime field.

SPHGen uses Jinja2 templates to generate a vectorized C library header that you can include in your project. Because SPHGen is a program generator, the target language can be changed. We demonstrate this by also targeting Jasmin as a backend, which enables security checks and generation of verified assembly.

## Repository layout

  -	`./gen.py`: main Python script. It computes optimal parameters for a given prime field and emits the final header at `./src/library.h`.
  -	`./templates/`: Jinja2 templates used by `gen.py` for code generation. The functions in the templates are explained in the paper.
  -	`./src/verify.py`: symbolic execution script to verify functional correctness.
  -	`./src/main.cpp`: benchmarking and testing code. Example of how to call the generated library.
  - `./others`: scripts to benchmark openssl and HACL*. Directory where we clone their repositories.

## In this README
  - **Dependencies**: installing Python packages, OpenSSL, HACL*, and Jasmin.
  - **Generation**: generating the library and running benchmarks.
  - **Benchmarking OpenSSL and HACL***: commands and wrappers we use to benchmark.
  - **Running the experiments from the paper**: scripts to run experiments, hardware setup, and plotting.

## Dependencies

We compile using `GCC 14.1.0` and use `Python 3.12.12` for the code generation.

Generating the library requires Jinja for template generation, sympy and numpy for verification. Install correct versions by executing `pip install -r requirements.txt`.

### Optional dependencies (for paper experiments)

We use NTL (Number Theoretic Library) for testing the correctness of the output. We follow the instructions from the [installation guide](https://libntl.org/doc/tour-unix.html). Example:

```
# starting from the root of the project
apt-get install libgmp3-dev                 # needed for NTL
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
# from the project rooth
cd others

# OpenSSL
git clone https://github.com/openssl/openssl
cd openssl/
./Configure 
make -j
cd ..

# starting from others/
# HACL*
git clone https://github.com/hacl-star/hacl-star
cd hacl-star/dist/gcc-compatible/
make -j
```

### Jasmin

SPHGen supports generating both C and [Jasmin](https://github.com/jasmin-lang/jasmin) code. Jasmin code can then either used for verification, or can be compiled to assembly. We install Jasmin using `opam install jasmin`, but other possibilities are available [here](https://github.com/jasmin-lang/jasmin/wiki/Installation-instructions). Version used `Jasmin Compiler 2025.02.1`. 
> **Note**: Jasmin only supports AVX2 instructions. No AVX512 and up.


## Generation

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
We give in `./others` the scripts using to benchmark OpenSSL and HACL*. They require installing the libraries in the same directory (see setup above). We give commands to run benchmarks for increasing size of messages:
  - `make bench_hacl` benchmarks hacl*. Requires `export LD_LIBRARY_PATH=$(pwd)/others/hacl-star/dist/gcc-compatible:$LD_LIBRARY_PATH`
  - `make bench_openssl` benchmarks openssl


## Running the experiments from the paper
We provide bash scripts that run the experiments from the paper, and jupyter notebooks that help with the plotting of the results.

We use `rdtsc` to measure cycles, see `src/tsc_x86.h` for details. To get accurate results we suggest [disabling frequency scaling](https://easyperf.net/blog/2019/08/02/Perf-measurement-environment-on-Linux#1-disable-turboboost).

```
# Intel
echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo
# AMD
echo 0 > /sys/devices/system/cpu/cpufreq/boost
```

### Our Setup

|||     
|----------|-------------|
| CPU |  Intel(R) Xeon(R) Silver 4410Y |
| Family | Sapphire-Rapids|
|Frequency| 2GHz|
|Turbo-Boost | Disabled |
|Hyperthreading| Disabled|
| Compiler | GCC 14.1.0|
| Python | Python 3.12.12 |
| OS | Ubuntu 22.04.5|

> **Note**: our performance model is hardcoded for our CPU. On different CPUs the model will likely need to be updated.    

### Benchmark various prime fields

SPHGen can generate a polynomial hash function for a given Crandall prime field. We take primes close to a power of two from this [list](https://t5k.org/lists/2small/). In the paper, we measure all prime fields from 100 to 400 bits. This takes a long time, around 20 seconds for each prime field on our machine. This means it takes around 1 hour 40 minutes to run one sweep. We measure for each ISA three different versions, this means 5 hours for each ISA. To run the full experiment, run `bench_sphgen.sh`. This runs the code for all ISAs by default.
The result of this script are saved in `sphgen_benchmarks`.

We currently do not have an automatic way of extracting cpu flags, so we give options to run partial experiments in case the host machine does not support all ISAs. Additionally, we give an option to run only a portion of experiments.
Here are all the options:
  - `-noavx512`         : disables avx512 experiments
  - `-noifma`           : disables AVX512IFMA experiments
  - `-nokaratsuba`      : disables karatsuba multiplication experiments
  - `stride <N>`        : run every N-th prime (for example stride 2 runs $\pi=101, 103, \dots$). Default value is 1.

### Benchmark poly1305 implementations

Similarly to the previous experiments, we also have a bash script to run the poly1305 implementations: `bench_poly1305.sh`. We run poly1305 for increasing size of the input message. For openSSL, we choose which version to run by setting the `OPENSSL_ia32cap` environment variable. The meaning of each bit can be found [here](https://github.com/openssl/openssl/blob/master/doc/man3/OPENSSL_ia32cap.pod). We give again options to run only specific versions.
  - `-noavx512`         : disables avx512 experiments
  - `-noifma`           : disables AVX512IFMA experiments
  - `-nokaratsuba`      : disables karatsuba multiplication experiments
  - `-noopenssl`        : skips openssl experiments
  - `-nohacl`           : skips hacl experiments

The result of this script are saved in `poly1305_benchmarks`. For each message size, the benchmark takes around 10 seconds, for 50 total message sizes. Hence the benchmark takes around 9 minutes for each implementation. We test our code for three different levels of unrolling. Meaning ~30 minutes for our versions. In total this script should take around 3 hours.

### Plotting

We provide a notebook `./plot.ipynb` that loads the results from the directories and generates the plots for the two experiments. 

## Artifact Evaluation

Here is a step by step guide for the artifact evalation.

### Prerequisites 

  -	OS: Ubuntu 22.04 (tested). macOS 14 is fine for code generation; benchmarking targets x86-64.
  - CPU: x86-64 with AVX2 (required). AVX-512/IFMA optional for those experiments.
  - Toolchain: GCC 14.1.0, Python 3.12.12, make, git.
  - Toolchain: Jinja2 for code generation, Sympy and Numpy for verifications.
  - (Optional) OpenSSL and HACL* for Poly1305 comparisons (see Dependencies).
  - (Optional) Jasmin (compiler 2025.02.1) for verification.

### Python dependencies

```
git clone https://github.com/tpegolotti/SPHGen
cd SPHGen
python3.12 -m venv env                            # optional make a virtual environment
source env/bin/activate
pip install -r requirements
```

### Quick test
Generate code and build a small binary for the Poly1305 prime ($2^{130}-5$):

```
make test PI=130 THETA=5 SIMD=4   # AVX2 path
````

This target builds a test binary for one prime. Run the produced binary (the Makefile prints its path). Expected: it completes without errors and prints no error messages during runtime.

### Hardware setup
We measure clock cycles from the time step counters using the `rdtsc` instruction. To obtain correct measurements, we suggest disabling frequency scaling. See [above](#running-the-experiments-from-the-paper) for the instructions.

### Reproduce paper experiments
We start by executing the parameter sweep of the full prime field range. 
A shorter sweep of all prime fields can be run by executing 
```
./bench_sphgen.sh stride 20
```
This takes a long time (see above).
A shorter sweep of all prime fields can be run by executing 
```
./bench_sphgen.sh stride 20
```

Full explanation of the script's options is given in the [Benchmark various prime fields](#benchmark-various-prime-fields) section.

Expected: after running the plotting script in `plot.ipynb`, the trends match the paper’s figures qualitatively.

### (Optional) Reproduce Poly1305 experiments

First, install OpenSLL and/or HACL* in the `./others` folder. See [Dependencies](#optional-dependencies-for-paper-experiments) for detailed instructions.
Second, run
```
./bench_poly1305.sh
```
to benchmark all versions.

### (Optional) Generate Jasmin Code

First, install Jasmin, see [Dependencies](#jasmin) for detailed instructions.
Then, running 
```
make test_jasmin PI=130 THETA=5 SIMD=4
```
generates a jasmin version, run security checks on it, and then compile it into assembly.

### Expected results
We provide CSV files for our results in the `.paper_results/` folder.

### Known Limitations
- At the time of writing, the performance model is tuned for Intel Sapphire Rapids. Latency and throughput parameters are not adjusted depending on the host machine.
- Auto detection of CPU flags is not implemented, the user needs to manually select which version to generate (or not to generate in case of the benchmarking scripts)