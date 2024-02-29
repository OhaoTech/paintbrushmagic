import os
import time
import webbrowser
from tempfile import NamedTemporaryFile


def jump(url, param, method='post'):
    # add parameters
    template = """<input type="hidden" name="{}" value="{}">"""
    tmp = ""
    for key, value in param.items():
        tmp += template.format(key, value)

    # html content including a form which used to jump
    html_content = f"""
    <html>
    <head><title>Redirecting...</title></head>
    <body onload="document.forms[0].submit()">
        <form action="{url}" method="{method}" id="searchForm">
            {tmp}
        </form>
    </body>
    </html>
    """
    # write html into temporary file
    with NamedTemporaryFile('w', delete=False, suffix='.html') as temp_file:
        temp_file.write(html_content)
        temp_file_path = temp_file.name

        # use browser open the bridge file
        webbrowser.open(temp_file_path)

    # wait for seconds
    time.sleep(1)
    # 删除临时文件
    os.remove(temp_file_path)


if __name__ == '__main__':
    jump("http://127.0.0.1:", {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6})
