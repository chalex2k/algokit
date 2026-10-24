# competitive-programming
Competitive programming journey  
Автоматизация рутины при решении задач по алгоритмам с codeforces и подобных сайтов.    

Функционал:  
1) создание новой директории
```just new 2048C```
2) type your code
3) test using unit tests via pytest ```just test```
4) test using files ```just test_files``` 
5) сгенерировать код для отправки ```just```

## Competitive Companion

Установите расширение
[Competitive Companion](https://github.com/jmerle/competitive-companion), затем запустите
локальный listener:

```bash
just companion
```

Откройте страницу задачи и нажмите кнопку расширения. Для Codeforces listener создаст
каталог вида `2247B`, выполнит те же действия, что и `just new 2247B`, и сохранит все
примеры в `in1.txt`/`out1.txt`, `in2.txt`/`out2.txt` и так далее.

По умолчанию сервер слушает только `127.0.0.1:10043`. Другой порт можно передать так:

```bash
just companion 12345
```

Этот порт также нужно добавить в настройку custom ports расширения.


