import argparse
import requests
import json
import pandas as pd
import os
from prettytable import PrettyTable

class QuakeQuery:
    """
    一个用于与360 Quake API交互，进行搜索并展示查询结果的类。
    """

    def __init__(self, api_key):
        """
        使用提供的API密钥初始化QuakeQuery对象。

        :param api_key: 访问360 Quake服务所需的API密钥。
        """
        self.api_key = api_key

    def perform_search(self, query, result_count, start_page):
        """
        使用指定的查询参数执行对360 Quake API的搜索。

        :param query: 搜索词或查询字符串。
        :param result_count: 每页要获取的结果数上限。
        :param start_page: 开始获取结果的页码索引。
        :return: 包含搜索结果的API JSON响应。
        """
        headers = {"X-QuakeToken": self.api_key}
        payload = {
            "query": query,
            "start": start_page,
            "size": str(result_count),
        }

        try:
            response = requests.post(
                url="https://quake.360.cn/api/v3/search/quake_service",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()  # 对非2xx状态码抛出异常
            return json.loads(response.text)
        except requests.RequestException as e:
            print(f"API请求过程中发生错误: {e}")
            raise

    def display_results(self, api_response, start_page, result_count, query_term):
        """
        以格式化的表格形式打印搜索结果。

        :param api_response: 包含搜索结果的360 Quake API JSON响应。
        :param start_page: 当前结果所在页码。
        :param result_count: 每页结果总数。
        :param query_term: 原始搜索查询。
        """
        print("\n")
        print(f"页码：第{api_response['meta']['pagination']['page_index']}页 共"
              f"{api_response['meta']['pagination']['page_size']}页 总数量："
              f"{api_response['meta']['pagination']['total']}个")
        print(f"查询内容：{query_term}")

        table = PrettyTable(["序号", "地址", "IP", "端口"])

        for index, item in enumerate(api_response["data"], start=1):
            # 检查是否存在"http"子项
            if "http" in item["service"]:
                table.add_row([
                    index,
                    item["service"]["http"]["host"],
                    item["ip"],
                    item["port"],
                ])
            else:
                print(f"警告：第{index}条结果的'service'结构中缺少'http'子项，跳过该条记录。")

        print(table)

    def parse_command_line_arguments(self):
        """
        解析用于搜索功能的命令行参数。
        """
        parser = argparse.ArgumentParser(
            description="例如：python 360QuakeForCMD.py --search IP 或 domain\t "
                        "python 360QuakeForCMD.py --search \"domain=xx.com\" 或 \"city=Beijing\"",
            prog="360QuakeForCMD.py",
        )

        group = parser.add_mutually_exclusive_group()
        group.add_argument("--version", "-V", action="version",
                           version=f"| %(prog)s Ver1.1|")

        parser.add_argument("--search", "-S", help="搜索关键词", type=str)
        parser.add_argument("--size", help="显示结果数量（默认为100）", default=100)
        parser.add_argument("--page", help="显示结果页码（默认为1）", default=1)

        return parser.parse_args()

    def main(self):
        # 解析命令行参数
        args = self.parse_command_line_arguments()

        if args.search:
            search_results = self.perform_search(args.search, args.size, args.page)
            self.display_results(search_results, args.page, args.size, args.search)

            # 直接导出到当前目录下，无需询问用户
            self.export_to_excel(search_results, args.search)
            print(f"结果已成功导出至当前目录下的quake_results_{args.search.replace(' ', '_').replace(':', '').replace('"', '')}.xlsx文件。")
        else:
            print("\nUsage: 360QuakeForCMD.py -h, --help 查看帮助信息并退出")

    def export_to_excel(self, api_response, query_term):
        """
        将搜索结果导出到当前工作目录下的Excel文件中，文件名包含当前查询语句以避免覆盖。

        :param api_response: 包含搜索结果的360 Quake API JSON响应。
        :param query_term: 当前搜索查询语句。
        """
        data = [
            (
                index + 1,
                item["service"]["http"]["host"],
                item["ip"],
                item["port"],
            )
            for index, item in enumerate(api_response["data"])
        ]

        df = pd.DataFrame(data, columns=["序号", "地址", "IP", "端口"])

        # 获取当前工作目录
        current_dir = os.getcwd()

        # 构建文件名，包含当前查询语句
        query_filename = query_term.replace(" ", "_").replace(":", "").replace('"', "")
        file_name = f"quake_results_{query_filename}.xlsx"

        # 构建文件路径
        file_path = os.path.join(current_dir, file_name)

        df.to_excel(file_path, index=False, engine="openpyxl")
        print(f"结果已成功导出至当前目录下的{file_name}文件。")

if __name__ == '__main__':
    # 作者：dreamhax
    QuakeQuery("Enter_Your_QuakeAPI").main()