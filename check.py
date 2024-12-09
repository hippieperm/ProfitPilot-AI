import os
import re
from bs4 import BeautifulSoup
from pathlib import Path

class WebProjectAnalyzer:
    def __init__(self, project_dir='.'):
        self.project_dir = Path(project_dir)
        self.html_files = []
        self.js_files = []
        self.css_files = []
        self.dependencies = {
            'html': {},  # html 파일별 의존성
            'missing_files': [],  # 존재하지 않는 파일
            'unused_files': []    # 참조되지 않는 파일
        }

    def scan_files(self):
        for file_path in self.project_dir.rglob('*'):
            if file_path.is_file():
                if file_path.suffix == '.html':
                    self.html_files.append(file_path)
                elif file_path.suffix == '.js':
                    self.js_files.append(file_path)
                elif file_path.suffix == '.css':
                    self.css_files.append(file_path)

    def analyze_html_dependencies(self):
        for html_file in self.html_files:
            self.dependencies['html'][str(html_file)] = {
                'js': [],
                'css': [],
            }
            
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                # JS 파일 분석
                scripts = soup.find_all('script', src=True)
                for script in scripts:
                    src = script['src']
                    self.dependencies['html'][str(html_file)]['js'].append(src)
                    
                # CSS 파일 분석
                links = soup.find_all('link', rel='stylesheet')
                for link in links:
                    href = link.get('href')
                    if href:
                        self.dependencies['html'][str(html_file)]['css'].append(href)

    def verify_dependencies(self):
        all_referenced_files = set()
        
        # HTML 파일에서 참조된 모든 파일 확인
        for html_file, deps in self.dependencies['html'].items():
            for js_file in deps['js']:
                js_path = self.project_dir / js_file.lstrip('/')
                if not js_path.exists():
                    self.dependencies['missing_files'].append(f"Missing JS: {js_file} in {html_file}")
                all_referenced_files.add(str(js_path))
                
            for css_file in deps['css']:
                css_path = self.project_dir / css_file.lstrip('/')
                if not css_path.exists():
                    self.dependencies['missing_files'].append(f"Missing CSS: {css_file} in {html_file}")
                all_referenced_files.add(str(css_path))
        
        # 사용되지 않는 파일 확인
        for js_file in self.js_files:
            if str(js_file) not in all_referenced_files:
                self.dependencies['unused_files'].append(f"Unused JS: {js_file}")
                
        for css_file in self.css_files:
            if str(css_file) not in all_referenced_files:
                self.dependencies['unused_files'].append(f"Unused CSS: {css_file}")

    def print_analysis(self):
        print("\n=== 웹 프로젝트 분석 결과 ===")
        
        print("\n📄 HTML 파일별 의존성:")
        for html_file, deps in self.dependencies['html'].items():
            print(f"\n{html_file}")
            print("  JS 파일:")
            for js in deps['js']:
                print(f"    - {js}")
            print("  CSS 파일:")
            for css in deps['css']:
                print(f"    - {css}")
        
        print("\n⚠️ 누락된 파일:")
        for missing in self.dependencies['missing_files']:
            print(f"  - {missing}")
        
        print("\n⚠️ 사용되지 않는 파일:")
        for unused in self.dependencies['unused_files']:
            print(f"  - {unused}")

def analyze_web_project(project_dir='.'):
    analyzer = WebProjectAnalyzer(project_dir)
    analyzer.scan_files()
    analyzer.analyze_html_dependencies()
    analyzer.verify_dependencies()
    analyzer.print_analysis()

if __name__ == '__main__':
    analyze_web_project()