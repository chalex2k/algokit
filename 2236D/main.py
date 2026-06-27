from fastio import *

def test_partition():
    for a, k, exp in (
        ([1, 2, 3], 3, [[1, 2, 3]]),
        ([1, 2, 3, 10], 3, [[1, 2, 3], [10]]),
    ):
        assert partition(a, k) == exp

def partition(a: list[int], k: int) -> list[list[int]]:
    a.sort()
    subarrs = []
    start = 0
    for i in range(1, len(a)):
        curr = a[i]
        pre = a[i-1]
        if curr - pre < 0 or curr - pre > k:
            subarrs.append(a[start: i])
            start = i
    subarrs.append(a[start:])
    return subarrs


def check(a: list[int]) -> bool:
    if a[0] != a[-1]:
        return True
    return len(a) % 2 == 0


def solve(a: list[int], k: int):
    parts = partition(a, k)
    for p in parts:
        if check(p):
            return YES
    return NO


def main():
    for _ in range(ii()):
        n, k = lii()
        a = lii()
        print(solve(a, k))


if __name__ == '__main__':
    main()
