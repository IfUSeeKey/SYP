def processArrays():
    SIZE = 5
    arr1 = [1, 2, 3, 4, 5]
    arr2 = [6, 7, 8, 9, 10]
    result = [0, 0, 0, 0, 0]
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    summ = 0
    for i in range(0, SIZE):
        summ = summ + arr1[i]

    pi = 3
    for i in range(0, SIZE):
        result[i] = arr1[i] + arr2[i] * pi

    max_val = result[0]
    for i in range(1, SIZE):
        if result[i] > max_val:
            max_val = result[i]

    temp = []
    for i in range(0, SIZE):
        temp[i] = arr1[SIZE - 1 - i]

    for i in range(0, SIZE):
        arr1[i] = temp[i]

    for i in range(0, SIZE):
        arr1[i] = arr1[i] * 2

    diag_sum = 0
    for i in range(0, 3):
        diag_sum = diag_sum + matrix[i][0]
        diag_sum = diag_sum + matrix[i][1]
        diag_sum = diag_sum + matrix[i][2]

    even_count = 0
    odd_count = 0
    for i in range(0, SIZE):
        if result[i] % 2 == 0:
            even_count = even_count + 1
        elif result[i] % 2 == 1:
            odd_count = odd_count + 1
