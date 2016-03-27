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
    params = simple_learn.read_parameters()
    write_data(params)

    # generate param file
    # with open("data", "wb") as fout:
        # 99 2 -5 7 6 4 5 5
        # bary = bytearray([99, 2, 0xFB, 7, 6, 4, 5, 5])
        # bary.append(0)
        # fout.write(bary)

if __name__ == '__main__':
    main()