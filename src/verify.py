import sympy as sp
import os

sp.init_printing()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def register_functions(file_contents):
    # look for the rows that contain @SPHVerify
    rows = []
    for line in file_contents.split('\n'):
        if '@SPHVerify' in line:
            rows.append(line)

    # split the rows using the func and endfunc tags
    funcs = {} # (pre, body, post)

    cur_func = ''
    for line in rows:
        if 'func' in line and not 'endfunc' in line:
            cur_func = line.split('func')[1].strip()
            cur_func = cur_func.split('*/')[0].strip()
            # print(f'Found function: {cur_func}')
            funcs[cur_func] = ([],[],[],[]) # pre, body, post, result
        elif 'endfunc' in line:
            cur_func = ''
        elif cur_func != '':
            if 'pre' in line:
                idx = 0
                stripped = line.split('pre')[1].strip()
                if '*/' in stripped:
                    stripped = stripped.split('*/')[0].strip()
                if stripped == '':
                    continue
            elif 'post' in line:
                idx = 2
                stripped = line.split('post')[1].strip()
                if '*/' in stripped:
                    stripped = stripped.split('*/')[0].strip()
                if stripped == '':
                    continue
            elif 'result' in line:
                idx = 3
                stripped = line.split('result')[1].strip()
            else:
                idx = 1
                stripped = line.split('@SPHVerify:')[1].strip()
                stripped = stripped.replace('.x', '')
                if '*/' in stripped:
                    stripped = stripped.split('*/')[0].strip()
                if stripped == '':
                    continue

            # parse special commands
            # if "for(" in stripped:


            funcs[cur_func][idx].append(stripped)
    return funcs

def oracle_carry_round(a_in, big, small, theta):
    a = a_in.copy()
    l = len(a)
    for i in range(l-1):
        a[i+1] += (a[i] / 2 ** big)
        a[i] %= (1 << big)
    a[0] += (a[l-1] / 2 ** small) * theta
    a[l-1] %= (1 << small)
    a[1] += (a[0] / 2 ** big)
    a[0] %= (1 << big)
    a[2] += (a[1] / 2 ** big)
    a[1] %= (1 << big)
    return a

def verify_functions(funcs):
    for f in funcs:
        code = ""

        # init the precondition
        pre = funcs[f][0]
        code += "".join(f"{line}\n" for line in pre)


        # exec the body
        body = funcs[f][1]
        code += "".join(f"{line}\n" for line in body)

        # verify the post
        post = funcs[f][2]
        code += "".join(f"{line}\n" for line in post)

        # print(code, flush=True)
        try:
            exec(code)
        except AssertionError as e:
            print(f'Function {f:<40} {bcolors.FAIL:>12}{bcolors.BOLD}FAILED{bcolors.ENDC}')
            continue

        # print green if it passed
        print(f'Function {f:<40} {bcolors.OKGREEN:>12}{bcolors.BOLD}PASSED{bcolors.ENDC}', flush=True)

def verify():
    # get directory of this file
    cwd = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(cwd, 'library.h')
    print(f'Verifying functions in {filename}', flush=True)
    # open the file src/library.h in read mode
    with open(filename, 'r') as file:
        # read the contents of the file
        file_contents = file.read()

    funcs = register_functions(file_contents)
    verify_functions(funcs)
    


if __name__ == '__main__':
    verify()
