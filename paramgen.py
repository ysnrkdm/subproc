import simple_learn


def conv_num(num):
    if num < 0:
        return 256 + num
    else:
        return num


def write_data(parameters):
    norm_params = map(conv_num, parameters)

    with open("data", "wb") as fout:
        bary = bytearray(norm_params)
        bary.append(0)
        fout.write(bary)


def main():
    # load parameter
    a = simple_learn.SimpleLearn()
    params = a.read_parameters()
    write_data(params)


if __name__ == '__main__':
    main()