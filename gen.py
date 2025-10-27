from jinja2 import Environment, FileSystemLoader
import argparse
import math


def eq_9(big, l, pi, theta_bits, new):
    """
    Compute the bit-growth residual from Equation 9 for the current operand layout.

    Args:
        big: Current bit-size allocated per limb.
        l: Number of limbs.
        pi: Prime field.
        theta_bits:  Log2-derived bit width for the `theta` parameter.
        new: Flag indicating whether to use the new constraint.

    Returns:
        Residual digits that indicate how close the current configuration is to the limit.
    """
    assert (new)  # making sure we benchmark the correct thing
    if not new:
        return 2 * big + l * big - pi + \
            theta_bits + math.floor(math.log2(l)) + 1
    else:
        return 2 * big + l * big - pi + theta_bits + math.ceil(math.log2(l))

def get_limb_size(pi, theta, ifma, kara, new_constraint):
    """
    Determine a limb size and maximum unroll factor that satisfy hardware constraints.
    Iteratively increases the limb count until both size and kappa bounds are met.

    Args:
        (pi, theta): Prime field.
        ifma: Whether AVX-512 IFMA instructions are available.
        kara: Whether Karatsuba multiplication should be used.
        new_constraint: Flag selecting the updated constraint rule.

    Returns:
        A tuple ``(big, max_unroll)`` where ``big`` is the limb size in bits and
        ``max_unroll`` is the maximum safe loop unroll factor.
    """
    if ifma:
        bits = 52
        limit = 128
    else:
        bits = 32
        limit = 64
    big = bits
    l = math.ceil(pi / big)
    big = math.ceil(pi / l)
    theta_bits = math.ceil(math.log2(theta))
    if not kara:
        res = eq_9(big, l, pi, theta_bits, new_constraint)
        kap = big + l * big - pi + theta_bits
    else:
        res = eq_9(big, l, pi, theta_bits, new_constraint)
        kap = 0
    while res >= limit or kap > bits:
        l += 1
        big = math.ceil(pi / l)
        if not kara:
            kap = big + l * big - pi + theta_bits
            res = eq_9(big, l, pi, theta_bits, new_constraint)
        else:
            res = eq_9(big, l, pi, theta_bits, new_constraint)
            kap = 0
    log_max_unroll = limit - res
    max_unroll = math.floor(2**log_max_unroll)
    return big, max_unroll

def get_parameters(
        pi,
        theta,
        simd_size,
        ifma=False,
        limit_unroll=8,
        kara=False,
        new_constraint=True):
    """
    Gather the primary tuning parameters used during template rendering.

    Args:
        (pi, theta): Prime field.
        simd_size: vector width of the target ISA.
        ifma: Whether AVX-512 IFMA instructions are available.
        limit_unroll: Upper bound on loop unrolling supplied by the caller.
        kara: Whether Karatsuba multiplication should be used.
        new_constraint: Flag selecting the updated constraint rule.

    Returns:
        Tuple containing derived block size, limb count, big/small limb widths,
        kappa value, capped unroll factor, padded precision, and remainder limb size.
    """
    block_size = math.floor(pi / 8)
    limb_size, max_unroll = get_limb_size(
        pi, theta, ifma, kara, new_constraint)
    max_unroll = min(max_unroll, limit_unroll)
    l = math.ceil(pi / limb_size)
    big = math.ceil(pi / l)
    small = pi - (l - 1) * big
    kappa = theta * 2**(big - small)
    pib = block_size * 8
    smallr = pib - (l - 1) * big
    return block_size, l, big, small, kappa, max_unroll, pib, smallr


def count_ones(a):
    """
    Count the number of set bits in an integer.

    Args:
        a: Integer whose population count is needed.

    Returns:
        Number of 1 bits present in ``a``.
    """
    count = 0
    bina = bin(a)
    for i in range(len(bina)):
        if bina[i] == '1':
            count += 1
    return count

def model(l, theta, unroll, simd_size, ifma, kara):
    """
    Estimate the number of cycles per iteration for the given prime field configuration.

    Args:
        l: Number of limbs.
        theta: prime field theta.
        unroll: Loop unroll factor to model.
        simd_size: vector width of the target ISA.
        ifma: Whether AVX-512 IFMA instructions are available.
        kara: Whether Karatsuba multiplication is be used.

    Returns:
        Estimated aggregate instruction count (cycles per iteration proxy).
    """
    pop_theta = count_ones(theta)
    if ifma:
        if simd_size == 8:
            matmuls = unroll * l * l
            gathers = unroll * ((8 / 3) * l + l - 1)
            carries = 4 * (l + 2) + pop_theta

            cpi = matmuls + gathers + carries
        else:
            raise ValueError("Invalid SIMD size")
    else:
        if simd_size == 4:
            if kara:
                matmuls = unroll * 2 * \
                    (2 * (math.ceil(l / 2)**2) + (math.floor(l / 2)**2)) / 3
                additions = (2 * math.floor(l / 2) - 1) * (pop_theta - 1)
                matmuls += additions
            else:
                matmuls = (2 * unroll * l * l - l) / 3
            gathers = unroll * (2 * l + l - 1)
            carries = 2 * (l + 2) + (pop_theta - 1)

            cpi = matmuls + gathers + carries
        elif simd_size == 8:
            if kara:
                matmuls = unroll * \
                    (2 * (math.ceil(l / 2)**2) + (math.floor(l / 2)**2)) + (math.floor(l / 2))
                addition = (2 * math.floor(l / 2) - 1) * (pop_theta)
                matmuls += addition
            else:
                matmuls = unroll * l * l
            gathers = unroll * ((8 / 3) * l + l - 1)
            carries = 2 * (l + 2) + pop_theta

            cpi = matmuls + gathers + carries
        else:
            raise ValueError("Invalid SIMD size")
    return cpi

def shift_right(x, n):
    """
    Apply a right-shift to expose Python's ``>>`` operator inside templates.
    
    Args:
        x: Integer to shift.
        n: Number of bits to shift right.

    Returns:
        Result of shifting ``x`` by ``n`` bits.
    """
    return x >> n

def gen(
        pi,
        theta,
        avx_512_ifma,
        simd_size,
        max_unroll,
        toprint,
        karatsuba,
        norun,
        jasmin,
        new_constraint):
    """
    Generate library sources for the requested configuration and optional Jasmin output.

    Args:
        (pi, theta): Prime field.
        avx_512_ifma: Whether AVX-512 IFMA instructions are available.
        simd_size: Native vector width (number of lanes) of the target ISA.
        max_unroll: Maximum loop unroll factor requested by the caller.
        toprint: Whether to print the computed parameters to stdout.
        karatsuba: Whether Karatsuba multiplication should be used.
        norun: When true, only print summary information.
        jasmin: Whether to render the Jasmin template in addition to C headers.
        new_constraint: Flag selecting the updated constraint rule.
    """
    environment = Environment(loader=FileSystemLoader("./templates"))
    block_size, l, big, small, kappa, unroll, pib, smallR = get_parameters(
        pi, theta, simd_size, avx_512_ifma, limit_unroll=max_unroll, kara=karatsuba, new_constraint=new_constraint)
    cpi = model(l, theta, unroll, simd_size, avx_512_ifma, karatsuba)
    if norun:
        print(f"{pi},{theta},{simd_size},{unroll},{round(cpi, 1)}")
        return
    if toprint:
        print(f"pi: {pi}, pi: {pib}, theta: {theta}, block_size: {block_size}, l: {l}, big: {big}, small: {small}, kappa: {kappa}, unroll: {unroll}, cpi: {cpi}, new_constraint: {new_constraint}")

    if jasmin:
        jasmin_template = environment.get_template("jasmin.j2")
        jasmin_content = jasmin_template.render(
            zip=zip,
            range=range,
            enumerate=enumerate,
            bin=bin,
            reversed=reversed,
            theta=theta,
            pi=pi,
            l=l,
            big=big,
            small=small,
            kappa=kappa,
            block_size=block_size,
            unroll=unroll,
            simd_size=simd_size,
            smallR=smallR,
            shift_right=shift_right,
            cpi=cpi,
            ceil=math.ceil,
            floor=math.floor,
            max=max,
            karatsuba=karatsuba
        )

        with open("src/library.jazz", mode="w", encoding="utf-8") as message:
            message.write(jasmin_content)

    template = environment.get_template("library.j2")
    content = template.render(
        zip=zip,
        range=range,
        enumerate=enumerate,
        bin=bin,
        reversed=reversed,
        ifma=avx_512_ifma,
        theta=theta,
        pi=pi,
        pib=pib,
        l=l,
        big=big,
        small=small,
        kappa=kappa,
        block_size=block_size,
        unroll=unroll,
        simd_size=simd_size,
        smallR=smallR,
        shift_right=shift_right,
        cpi=cpi,
        ceil=math.ceil,
        floor=math.floor,
        max=max,
        karatsuba=karatsuba,
        jasmin=jasmin
    )

    with open("src/library.h", mode="w", encoding="utf-8") as message:
        message.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pi", type=int, required=True)
    parser.add_argument("-t", "--theta", type=int, required=True)
    parser.add_argument("-s", "--simd", default=4, type=int, required=True)
    parser.add_argument("-u", "--unroll", default=-1, type=int, required=False)
    parser.add_argument(
        "-k",
        "--karatsuba",
        default=False,
        action="store_true")
    parser.add_argument("-j", "--jasmin", default=False, action="store_true")
    parser.add_argument("-pr", "--print", default=False,
                        help="Print generated code", action="store_true")
    parser.add_argument(
        "-m",
        "--madd",
        default=False,
        help="Use AVX-512 IFMA madd instruction",
        action="store_true")
    parser.add_argument("-n", "--no-run", default=False,
                        help="Do not run the code", action="store_true")
    parser.add_argument("-nc", "--newconstraint", default=True,
                        help="Use new constraint", action="store_false")
    args = parser.parse_args()

    gen(args.pi, args.theta, args.madd, args.simd, args.unroll, args.print,
        args.karatsuba, args.no_run, args.jasmin, args.newconstraint)
