import sympy as sp
import os

sp.init_printing()


class bcolors:
    """ANSI color helpers to style terminal output."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def register_ops(file_contents):
    """Collect operation signatures declared with ``@SPHVerify``.

    Parameters
    ----------
    file_contents : file contents to verify.

    Returns
    -------
    dict[str, tuple[list[str], str]]
        Mapping from operation name to argument list and Python body string.
    """
    # look for the rows that contain @SPHVerify
    rows = []
    for line in file_contents.split('\n'):
        if '@SPHVerify' in line:
            rows.append(line)

    # split the rows using the func and endfunc tags
    ops = {}  # (pre, body, post)

    cur_op = ''
    for line in rows:
        if ' op ' in line:
            cur_op = line.split('op')[1].strip()
            cur_op = cur_op.split('*/')[0].strip()
            params = cur_op.split('(')[1].split(')')[0].split(',')
            body = cur_op.split(':')[1].strip()
            cur_op = cur_op.split('(')[0].strip()
            ops[cur_op] = (params, body)  # parameters, body

    return ops


def register_functions(file_contents):
    """Collect function verification blocks declared with ``@SPHVerify``.

    Parameters
    ----------
    file_contents : file contents to verify.

    Returns
    -------
    dict[str, tuple[list[str], list[str], list[str]]]
        Mapping from function name to (pre, body, post) instruction lists.
    """
    # look for the rows that contain @SPHVerify
    rows = []
    toappend = False
    for line in file_contents.split('\n'):
        if '@SPHVerify: func' in line or toappend:
            rows.append(line)
            if 'endfunc' in line:
                toappend = False
            else:
                toappend = True

    # split the rows using the func and endfunc tags
    funcs = {}  # (pre, body, post)

    cur_func = ''
    for line in rows:
        if 'func' in line and 'endfunc' not in line:
            cur_func = line.split('func')[1].strip()
            cur_func = cur_func.split('*/')[0].strip()
            # print(f'Found function: {cur_func}')
            funcs[cur_func] = ([], [], [])  # pre, body, post
        elif 'endfunc' in line:
            cur_func = ''
        elif 'const' in line:
            # initialize constants at the start of the function (for example for the masks)
            # TODO
            continue
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
            elif 'ignore' in line:
                continue
            else:
                idx = 1
                stripped = line.replace('.', '')
                # remove everything after the first semicolon
                stripped = stripped.split(';')[0].strip()
                if '*/' in stripped:
                    stripped = stripped.split('*/')[0].strip()
                if stripped == '':
                    continue

            # parse special commands
            # if "for(" in stripped:
            stripped = stripped.replace('->', '    ')

            funcs[cur_func][idx].append(stripped)
    return funcs


def generate_ops(ops):
    """Emit Python code for the operations.

    Parameters
    ----------
    ops : dict[str, tuple[list[str], str]]
        Operation definitions produced by ``register_ops``.
    funcs : dict[str, tuple[list[str], list[str], list[str]]]
        Function verification snippets produced by ``register_functions``.

    Returns
    -------
    str
        Standalone Python code that implements the Jasmin operations.
    """
    code = "import sympy as sp\nimport numpy as np\n\n"
    # generate the code for the operations
    for op in ops:
        params, body = ops[op]
        code += f"def {op}({', '.join(params)}):\n"
        code += f"    {body}\n\n"

    return code


def oracle_carry_round(a_in, big, small, theta):
    """Reference implementation for the carry_round Jasmin primitive."""
    a = a_in.copy()
    l = len(a)
    for i in range(l - 1):
        a[i + 1] += (a[i] / 2 ** big)
        a[i] %= (1 << big)
    a[0] += (a[l - 1] / 2 ** small) * theta
    a[l - 1] %= (1 << small)
    a[1] += (a[0] / 2 ** big)
    a[0] %= (1 << big)
    a[2] += (a[1] / 2 ** big)
    a[1] %= (1 << big)
    return a


def verify_functions(code, funcs):
    """Execute the generated helpers against verification snippets.

    Parameters
    ----------
    code : str
        Python source created by ``generate_ops`` to materialise the ops.
    funcs : dict[str, tuple[list[str], list[str], list[str]]]
        Verification sequences keyed by function name.
    """
    for f in funcs:
        # Given the ops in 'code', generate the function code to test
        code_to_test = code + "\n"

        # init the precondition
        pre = funcs[f][0]
        code_to_test += "".join(f"{line}\n" for line in pre)

        # gen the body
        body = funcs[f][1]
        code_to_test += "".join(f"{line}\n" for line in body)

        # add the post
        post = funcs[f][2]
        code_to_test += "".join(f"{line}\n" for line in post)

        # print the code to a file and execute it
        # if .tmp doesn't exist, create it
        tmp_dir = os.path.join(os.path.dirname(__file__), '.tmp')
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        tmp_file = os.path.join(tmp_dir, f'{f}.py')
        with open(tmp_file, 'w') as file:
            file.write(code_to_test)

        # print(f'Executing {tmp_file}', flush=True)
        # execute the file
        import subprocess
        result = subprocess.run(['python3', tmp_file])
        if result.returncode != 0:
            print(f'Function {f:<40} {bcolors.FAIL:>12}{bcolors.BOLD}FAILED{bcolors.ENDC}')
            continue
        else:
            print(f'Function {f:<40} {bcolors.OKGREEN:>12}{bcolors.BOLD}PASSED{bcolors.ENDC}',flush=True)



def verify():
    # get directory of this file
    cwd = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(cwd, 'library.h')
    print(f'Verifying functions in {filename}', flush=True)
    # open the file src/library.h in read mode
    with open(filename, 'r') as file:
        # read the contents of the file
        file_contents = file.read()

    ops = register_ops(file_contents)
    funcs = register_functions(file_contents)
    code = generate_ops(ops)
    verify_functions(code, funcs)


if __name__ == '__main__':
    verify()
