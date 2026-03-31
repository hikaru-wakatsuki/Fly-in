def parentheses_check(line: str) -> bool:
    tmp: list = []
    for c in line:
        if c == '(':
            tmp.append(c)
        elif c == '{':
            tmp.append(c)
        elif c == '}':
            if not tmp:
                return False
            check_c: str = tmp.pop()
            if check_c != '{':
                return False
        elif c == ')':
            if not tmp:
                return False
            check_c: str = tmp.pop()
            if check_c != '(':
                return False
    if tmp:
        return False
    return True


def list_next_check(lst: list[int]) -> int:
    count: int = 0
    before_i: int | None = None
    for i in lst:
        if before_i is not None:
            if i - before_i == 1:
                count += 1
        before_i = i
    return count


def reverse_list(lst: list[int]) -> list[int]:
    index: int = len(lst)
    result: list[int] = []
    while index > 0:
        index -= 1
        result.append(lst[index])
    return result


def list_join_sort(lst1: list[int], lst2: list[int]) -> list[int]:
    result: list[int] = []
    for i in lst1:
        result.append(i)
    for i in lst2:
        result.append(i)
    result.sort()
    return result


def change_alpha(line: str) -> str:
    i: int = 0
    result: str = ""
    for c in line:
        if c.isalpha():
            if i % 2 == 0:
                c = c.lower()
            else:
                c = c.upper()
            i += 1
        result += c
    return result


def convert_string(line: str, i: int) -> str:
    result = ""
    lower: str = "abcdefghijklmnopqrstuvwxyz"
    upper: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for c in line:
        if c.islower():
            for j in range(len(lower)):
                if c == lower[j]:
                    c = lower[(i + j) % len(lower)]
        elif c.isupper():
            for j in range(len(upper)):
                if c == upper[j]:
                    c = upper[(i + j) % len(upper)]
        result += c
    return result


def count_same_check(line: str) -> bool:
    dct: dict[str, int] = {}
    for c in line:
        if not c in dct:
            dct[c] = 1
        elif c in dct:
            dct[c] += 1
    if not dct:
        return True
    lst: list = list(dct.values())
    check: int = lst[0]
    for i in dct.values():
        if check != i:
            return False
    return True
