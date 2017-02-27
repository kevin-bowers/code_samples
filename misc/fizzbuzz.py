#!/usr/bin/env python


def main():
    for num in range(1, 101):
        if (num % 3 == 0) and (num % 5 == 0):
            output = 'FizzBuzz'
        elif num % 3 == 0:
            output = 'Fizz'
        elif num % 5 == 0:
            output = 'Buzz'
        else:
            output = num
        print output

if __name__ == '__main__':
    main()
