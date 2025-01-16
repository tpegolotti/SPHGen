#include <iostream>
#include <vector>
#include <random>
#include <gmp.h>
#include "eval_ntl.h"
#include <NTL/ZZ.h>
#include <chrono>
#include "tsc_x86.h"
#include <functional>
#include <algorithm>
#include <iomanip>
#include "library.h"
using namespace NTL;

ZZ initialize(int degree, unsigned char* in_str,  ZZ* in_zz, bigint* in){
    SetSeed(ZZ(0));

    for (int i = 0; i < degree; i++){
#ifdef TEST
        ZZ val = (ZZ(1) << _PIB) - 1;
#else
        ZZ val = RandomBits_ZZ(_PIB);
#endif
        ZZ old_val = val;
        in_zz[i] = val;
        for (int j = 0; j < _BLOCK; j++){
            in_str[i * _BLOCK + j] = old_val % 256;
            old_val >>= 8;
        }
        for (int j = 0; j < _L-1; j++){
            in[i].x[j] = val % (1L << _BIG);
            val >>= _BIG;
        }
        in[i].x[_L-1] = val % (1L << SMALLR);
    }

#ifdef TEST
    return (ZZ(1) << _PIB) - _THETA - 1;
#else
    return RandomBits_ZZ(_PIB);
#endif
}

template <typename F, typename T, typename K>
double benchmark(F f, T* in, K* key, K* res, int degree, std::string name){
    std::cout << std::fixed;
    std::vector<double> times;

    myInt64 start, end;
    const int repetitions = 10;
    const double cycles_req = 1e9;

    double multiplier = 2;
    int num_runs = 10;

    while (multiplier > 1){
        double cycles = 0;
        start = start_tsc();
        for (int i = 0; i < num_runs; i++){
            f(in, *key, res, degree);
        }
        end = stop_tsc(start);
        multiplier = cycles_req / ((double) end);
        num_runs = (int) (num_runs * multiplier);
    }

    for (int i = 0; i < repetitions; i++){
        start = start_tsc();
        for(int j = 0; j < num_runs; j++){
            f(in, *key, res, degree);
        }
        end = stop_tsc(start);
        times.push_back((double) end / num_runs);
    }

    std::sort(times.begin(), times.end());
    return times[times.size() / 2];
}

int main(int argc, char* argv[]){
    if (argc != 2){
        std::cerr << "Usage: " << argv[0] << " <degree>" << std::endl;
        return 1;
    }
    
    int degree = std::stoi(argv[1]);
    int string_length = degree * _BLOCK;   

    unsigned char* in_str = (unsigned char*)malloc(string_length);

    bigint* in = (bigint*)malloc(degree * sizeof(bigint));
    ZZ* in_zz = (ZZ*)malloc(degree * sizeof(ZZ));
    bigint res, res_horner;
    ZZ* res_zz = (ZZ*)malloc(sizeof(ZZ));
    bigint oracle;

    ZZ key_zz = initialize(degree, in_str, in_zz, in);
    ZZ key_ntl = key_zz;
    bigint key;
    for (int i = 0; i < _L; i++){
        key.x[i] = key_ntl % (1L << _BIG);
        key_ntl >>= _BIG;
    }

#ifndef TEST
    double start = benchmark(eval, in_str, &key, &res, _SIMD, "PolyGen");
    // double start = 0;
    double mine = benchmark(eval, in_str, &key, &res, degree, "PolyGen");
    eval_ntl(in_zz, key_zz, res_zz, degree);
    auto cpi = (mine - start) / ((degree - _SIMD) / (_SIMD*_UNROLL));
    auto bpc = string_length / (mine - start);
    double model_bpc = string_length / (_CPI * (degree - _SIMD) / (_SIMD*_UNROLL));
    auto err = std::abs(cpi - _CPI) / cpi;
    std::cout << _PI << ","  << _THETA << "," << _L << "," << _UNROLL << "," << _SIMD << "," << degree << "," << string_length << "," << mine - start << "," << _CPI << "," << cpi << "," << cpi - _CPI << "," << err << "," << (double)(cpi - _CPI) / std::max(1,_UNROLL-1)  << std::endl;
#else
    std::cout << "Degree: " << degree << std::endl;
    eval(in_str, key, &res, degree);
    eval_ntl(in_zz, key_zz, res_zz, degree);
#endif

    for (int i = 0; i < _L; i++){
        oracle.x[i] = *res_zz % (1L << _BIG);
        *res_zz >>= _BIG;
    }

    if (!equal(&res, &oracle)){
        std::cerr << "Results do not match" << std::endl;
        return 1;
    }
    return 0;
}
