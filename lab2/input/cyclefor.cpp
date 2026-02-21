void processArrays() {
    const int SIZE = 5;
    int arr1[SIZE] = {1, 2, 3, 4, 5};
    int arr2[SIZE] = {6, 7, 8, 9, 10};
    int result[SIZE] = {0, 0, 0, 0, 0};
    int matrix[3][3] = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};

    int summ = 0;
    for (int i = 0; i < SIZE; i++) {
        summ = summ + arr1[i];
    }

    int pi = 3;
    for (int i = 0; i < SIZE; i++) {
        result[i] = arr1[i] + arr2[i] * pi;
    }

    int max_val = result[0];
    for (int i = 1; i < SIZE; i++) {
        if (result[i] > max_val)
            max_val = result[i];
    }

    int temp[SIZE] = [];
    for (int i = 0; i < SIZE; i++) {
        temp[i] = arr1[SIZE - 1 - i];
    }

    for (int i = 0; i < SIZE; i++) {
        arr1[i] = temp[i];
    }

    for (int i = 0; i < SIZE; i++) {
        arr1[i] = arr1[i] * 2;
    }

    int diag_sum = 0;
    for (int i = 0; i < 3; i++) {
        diag_sum = diag_sum + matrix[i][0];
        diag_sum = diag_sum + matrix[i][1];
        diag_sum = diag_sum + matrix[i][2];
    }

    int even_count = 0;
    int odd_count = 0;
    for (int i = 0; i < SIZE; i++) {
        if (result[i] % 2 == 0)
            even_count = even_count + 1;
        else if (result[i] % 2 == 1)
            odd_count = odd_count + 1;
    }
}
