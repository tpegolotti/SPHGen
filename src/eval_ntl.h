#include <NTL/ZZ.h>
#include "library.h"

using namespace NTL;

void pprint_ZZ(ZZ a){
    for (int i = 0; i < _L; i++){
        std::cout << a % (ZZ(1) << _BIG) << " ";
        a >>= _BIG;
    }
    std::cout << std::endl;
}

void eval_ntl(ZZ* in, ZZ key, ZZ* res, int degree){
    *res = in[0];
    ZZ modulo = (ZZ(1) << _PI) - _THETA;
    ZZ tmp;
    *res |= (ZZ(1) << _PIB);
    for (int i = 1; i < degree; i++){
        tmp = in[i];
        tmp |= (ZZ(1) << _PIB);
        *res = (*res * key + tmp) % modulo;
    }
}
