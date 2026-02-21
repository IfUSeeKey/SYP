# находит конец блока, который заканчивается на '}'
def findBlockEnd(lines, i):
    braceCount = 0
    while i < len(lines):
        line = lines[i]
        braceCount += line.count('{')
        braceCount -= line.count('}')
        if braceCount == 0 and '}' in line:
            return i + 1
        i += 1

# переводит c++ struct в python class
def translateStruct(lines, i):
    structLines, fields = [], []
    structName = lines[i].split()[1]
    for j in range(i + 1, len(lines)):
        line = lines[j].strip()
        if line == '};':
            break
        fieldType, fieldName = line.rstrip(';').split()
        fields.append((fieldName, fieldType))

    structLines.append(f'class {structName}:')
    structLines.append('    def __init__(self):')

    for fieldName, fieldType in fields:
        if fieldType == 'string':
            structLines.append(f'        self.{fieldName} = ""')
        elif fieldType == 'int' or fieldType == 'double':
            structLines.append(f'        self.{fieldName} = 0')
        else:
            structLines.append(f'        self.{fieldName} = None')
    structLines.append('')
    return structLines

# переводит функцию из с++ в Python
def translateFunction(lines, i):
    funcLines = []
    funcName, paramsStr = lines[i].strip().split('(')
    funcName = funcName.split()[1]
    paramsStr = paramsStr[:-3].split(',')
    pythonParams = ''
    for param in paramsStr:
        if param:
            pythonParams += param.split()[1] + ', '
    funcLines.append(f'def {funcName}({pythonParams[:-2]}):')
    i += 1

    startIndex = i - 1
    while i < findBlockEnd(lines, startIndex) - 1:
        line = lines[i].strip()
        if not line:
            funcLines.append('')
        else:
            statementLines, i = translateStatement(lines, i)
            if statementLines:
                for j in range(0, len(statementLines)):
                    funcLines.append('    ' + statementLines[j])
        i += 1
    funcLines.append('')
    return funcLines

# переводит код внутри функции или внутри другого блока
def translateStatement(lines, i):
    line = lines[i].strip().rstrip(';')
    if not line:
        return '', i
    elif line.startswith('if'):
        ifLines = [f'if {lines[i].rstrip('{').strip()[4:-1]}:']
        lastIndex = i
        for j in range(i + 1, len(lines)):
            lastIndex = j
            line = lines[j]
            if line == '}':
                break
            elif line == '    }':
                lastIndex -= 1
                break
            line = line.strip()
            if line.startswith('else if'):
                ifLines.append(f'elif {lines[j].rstrip('{').strip()[9:-1]}:')
            elif line.startswith('else'):
                ifLines.append(f'else:')
            else:
                a, j = translateStatement(lines, j)
                lastIndex = j
                for k in range(0, len(a)):
                    ifLines.append('    ' + a[k])
        return ifLines, lastIndex
    elif line.startswith('for'):
        forLines = []
        forCondition = line[5:-3].split(';')
        forLines.append(f'for {forCondition[0].split()[1]} in range({forCondition[0].split()[3]}, {forCondition[1].split()[2]}):')
        lastIndex, j = i, i + 1
        while j < len(lines):
            line = lines[j].strip()
            if line == '}':
                break
            a, j = translateStatement(lines, j)
            lastIndex = j
            for k in range(0, len(a)):
                forLines.append('    ' + a[k])
            j += 1
        return forLines, lastIndex + 1
    elif line.startswith('return'):
        value = line[7:].replace('true', 'True').replace('false', 'False')
        if value:
            return [f'return {value}'], i
        else:
            return ['return'], i
    else:
        if line == '}':
            return '', i
        line = line.replace('->', '.')
        line = line.replace('true', 'True').replace('false', 'False')
        line = line.replace('{', '[').replace('}', ']')
        if '=' in line:
            parts = line.split('=')
            if len(parts[0].split()) > 1:
                parts[0] = parts[0].split()[-1]
                parts[0] = parts[0].split('[')[0]
            return [f'{parts[0].strip()} = {parts[1].strip()}'], i
        line = line.replace('++', ' += 1').replace('--', ' -= 1')
        return [line], i

# перевод с++ кода
def translate(cppCode):
    lines, pythonLines, i = cppCode.split('\n'), [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('#include') or line.startswith('using'):
            i += 1
        elif line.startswith('//'):
            pythonLines.append('# ' + line[2:])
            i += 1
        elif line.startswith('struct'):
            pythonLines.extend(translateStruct(lines, i))
            i = findBlockEnd(lines, i)
        elif '(' in line and ')' in line and not line.endswith(';'):
            pythonLines.extend(translateFunction(lines, i))
            i = findBlockEnd(lines, i)
        else:
            pythonLines.append(line)
            i += 1
    return '\n'.join(pythonLines)

# старт
if __name__ == "__main__":
    with open('input/cyclefor.cpp') as input1:
        with open('output/cyclefor.py', 'w') as cyclefor:
            cyclefor.write(translate(input1.read()))

    with open('input/ifelse.cpp') as input2:
        with open('output/ifelse.py', 'w') as ifelse:
            ifelse.write(translate(input2.read()))

    with open('input/structura.cpp') as input3:
        with open('output/structura.py', 'w') as structura:
            structura.write(translate(input3.read()))
