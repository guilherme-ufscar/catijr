email = 'guilherme.rampazzo@estudante.ufscar.br'
nome = 'guilherme'
print(email.find('@'))
print(email.startswith('gui'))
print(email.count('a'))
print(type(email))
print(email.isnumeric())
print(email.isalpha())
print(nome.isalpha())

animal = 'c        a        c        h o r r o'
animal = animal.strip(' ')
print(animal)