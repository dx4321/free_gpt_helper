

def format_code(text: str) -> str:
    """ Преобразовать текст в код """

    if '\n' in text:
        # Разбиваем текст на строки
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False

        # Обходим все строки
        for line in lines:
            # Проверяем, начинается ли строка с ''' и не находимся ли мы уже внутри блока кода
            if line.startswith("```") and not in_code_block:
                # Если да, то помечаем, что мы находимся внутри блока кода
                in_code_block = True
                # Заменяем ''' на открывающий тег <code>
                line = line.replace("```", "<pre><code>")
            # Проверяем, заканчивается ли строка на ''' и находимся ли мы внутри блока кода
            elif line.endswith("```") and in_code_block:
                # Если да, то помечаем, что мы вышли из блока кода
                in_code_block = False
                # Заменяем ''' на закрывающий тег </code>
                line = line.replace("```", "</code></pre>")

            formatted_lines.append(line)

        # Объединяем отформатированные строки обратно в текст и возвращаем результат
        return '\n'.join(formatted_lines)
    else:
        return text
