#!/usr/bin/env python3
"""
IDM-VTON API 测试脚本

使用方法:
    python test_api.py                          # 测试本地服务
    python test_api.py --url <api-url>          # 测试远程服务
    python test_api.py --quick                  # 快速测试（跳过虚拟试穿）
"""
import argparse
import requests
import time
import sys
from pathlib import Path
from typing import Optional


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class APITester:
    """API测试器"""

    def __init__(self, base_url: str, quick_mode: bool = False):
        self.base_url = base_url.rstrip('/')
        self.quick_mode = quick_mode
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": []
        }

    def print_header(self, text: str):
        """打印测试标题"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

    def print_test(self, name: str):
        """打印测试名称"""
        print(f"{Colors.OKBLUE}🧪 测试: {name}{Colors.ENDC}")

    def print_success(self, message: str):
        """打印成功消息"""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
        self.results["passed"] += 1

    def print_error(self, message: str):
        """打印错误消息"""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
        self.results["failed"] += 1

    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

    def print_info(self, message: str):
        """打印信息"""
        print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

    def test_health(self) -> bool:
        """测试健康检查端点"""
        self.print_test("健康检查")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()

            data = response.json()
            self.print_success(f"服务状态: {data.get('status', 'unknown')}")

            # 检查Replicate配置
            if data.get('replicate_configured'):
                self.print_success("Replicate API已配置")
            else:
                self.print_warning("Replicate API未配置")

            return True

        except requests.exceptions.RequestException as e:
            self.print_error(f"健康检查失败: {str(e)}")
            return False

    def test_info(self) -> bool:
        """测试服务信息端点"""
        self.print_test("获取服务信息")

        try:
            response = requests.get(f"{self.base_url}/api/vton/info", timeout=10)
            response.raise_for_status()

            data = response.json()
            self.print_success(f"模型: {data.get('model', 'unknown')}")
            self.print_info(f"描述: {data.get('description', 'N/A')}")

            categories = data.get('categories', [])
            self.print_info(f"支持类别: {', '.join(categories)}")

            return True

        except requests.exceptions.RequestException as e:
            self.print_error(f"获取信息失败: {str(e)}")
            return False

    def test_try_on(self) -> bool:
        """测试虚拟试穿API"""
        if self.quick_mode:
            self.print_warning("跳过虚拟试穿测试（快速模式）")
            self.results["skipped"] += 1
            return True

        self.print_test("虚拟试穿API")

        # 查找测试图片
        test_data_dir = Path("test_data/test_data")
        model_dir = test_data_dir / "model"
        clother_dir = test_data_dir / "clother"

        if not test_data_dir.exists():
            self.print_warning("测试数据目录不存在，跳过虚拟试穿测试")
            self.print_info("提示: 创建 test_data/test_data/ 目录并放入测试图片")
            self.results["skipped"] += 1
            return True

        # 查找第一个可用的图片
        model_images = list(model_dir.glob("*.jpg")) + list(model_dir.glob("*.jpeg")) + list(model_dir.glob("*.png"))
        clother_images = list(clother_dir.glob("*.jpg")) + list(clother_dir.glob("*.jpeg")) + list(clother_dir.glob("*.png"))

        if not model_images or not clother_images:
            self.print_warning("未找到测试图片，跳过虚拟试穿测试")
            self.results["skipped"] += 1
            return True

        model_image = model_images[0]
        clother_image = clother_images[0]

        self.print_info(f"模特图片: {model_image.name}")
        self.print_info(f"衣服图片: {clother_image.name}")

        try:
            # 上传文件测试
            with open(model_image, 'rb') as person_file, \
                 open(clother_image, 'rb') as garment_file:

                files = {
                    'person_image': (model_image.name, person_file, 'image/jpeg'),
                    'garment_image': (clother_image.name, garment_file, 'image/jpeg')
                }

                data = {
                    'garment_description': 'shirt',
                    'category': 'upper_body',
                    'denoise_steps': 30
                }

                self.print_info("正在调用API... (这可能需要20-40秒)")
                start_time = time.time()

                response = requests.post(
                    f"{self.base_url}/api/vton/try-on/upload",
                    files=files,
                    data=data,
                    timeout=120  # 2分钟超时
                )

                elapsed = time.time() - start_time

                response.raise_for_status()
                result = response.json()

                if result.get('success'):
                    self.print_success(f"虚拟试穿成功！耗时: {elapsed:.1f}秒")
                    self.print_info(f"输出URL: {result.get('output_url', 'N/A')[:80]}...")

                    input_size = result.get('input_size', {})
                    if input_size:
                        self.print_info(
                            f"输入大小: 模特 {input_size.get('person_kb', 0)}KB, "
                            f"衣服 {input_size.get('garment_kb', 0)}KB"
                        )

                    return True
                else:
                    self.print_error(f"虚拟试穿失败: {result.get('error', 'Unknown')}")
                    return False

        except requests.exceptions.Timeout:
            self.print_error("请求超时（超过2分钟）")
            return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"API调用失败: {str(e)}")
            return False
        except FileNotFoundError as e:
            self.print_error(f"文件未找到: {str(e)}")
            return False

    def test_try_on_json(self) -> bool:
        """测试JSON格式的虚拟试穿API"""
        if self.quick_mode:
            self.print_warning("跳过JSON格式测试（快速模式）")
            self.results["skipped"] += 1
            return True

        self.print_test("JSON格式虚拟试穿")

        # 使用公开的测试图片URL（如果有）
        self.print_warning("需要提供图片URL才能测试此功能")
        self.print_info("示例: 使用公开的图片URL作为person_image和garment_image")
        self.results["skipped"] += 1
        return True

    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("IDM-VTON API 测试")
        print(f"🔗 测试URL: {self.base_url}")

        if self.quick_mode:
            print(f"{Colors.WARNING}⚡ 快速模式：跳过虚拟试穿测试{Colors.ENDC}")

        print()

        # 运行测试
        tests = [
            ("健康检查", self.test_health),
            ("服务信息", self.test_info),
            ("虚拟试穿", self.test_try_on),
            ("JSON格式", self.test_try_on_json),
        ]

        for name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.print_error(f"测试 '{name}' 发生异常: {str(e)}")
            print()  # 空行分隔

        # 打印总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")

        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]

        print(f"总计: {total} 个测试")
        print(f"{Colors.OKGREEN}✅ 通过: {self.results['passed']}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ 失败: {self.results['failed']}{Colors.ENDC}")
        print(f"{Colors.WARNING}⏭️  跳过: {self.results['skipped']}{Colors.ENDC}")

        # 成功率
        if total > 0:
            success_rate = (self.results["passed"] / (self.results["passed"] + self.results["failed"])) * 100 \
                if (self.results["passed"] + self.results["failed"]) > 0 else 100
            print(f"\n成功率: {success_rate:.1f}%")

        # 返回码
        exit_code = 0 if self.results["failed"] == 0 else 1

        if exit_code == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  部分测试失败{Colors.ENDC}")

        print()
        return exit_code


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="IDM-VTON API 测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_api.py                                    # 测试本地服务
  python test_api.py --url https://your-app.railway.app # 测试远程服务
  python test_api.py --quick                            # 快速测试
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='API基础URL（默认: http://localhost:8000）'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速模式：跳过虚拟试穿测试'
    )

    args = parser.parse_args()

    # 创建测试器并运行
    tester = APITester(args.url, quick_mode=args.quick)
    exit_code = tester.run_all_tests()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
