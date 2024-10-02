# Принцип обработки команд/запросов


1. Вызов команды инстанса основанного из метакласса `ApplicationMeta` и контекста `Context`
2. Запуск команды `execute` с передачей параметров. `self.context.execute(<params>)`
3. Передача управления в текущую стратегию, основанную на `BaseStrategy` в метод `execute` с передачей всех параметров
4. Стратегия обрабатывает параметры команды, и формирует результат обработки, который затем перенаправляется в точку вызова.