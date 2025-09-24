import requests
import json
import androidhelper
import time

class DictationApp:
    def __init__(self):
        self.droid = androidhelper.Android()
        self.data_url = "https://raw.githubusercontent.com/SoWarmhome/Mercy/refs/heads/main/Dictation/Dictation.json"
        self.data = None
        self.current_items = []
        self.current_index = 0
        
    def load_data(self):
        """从GitHub加载数据"""
        try:
            response = requests.get(self.data_url)
            response.encoding = 'utf-8'
            self.data = json.loads(response.text)
            return True
        except Exception as e:
            self.droid.makeToast(f"数据加载失败: {str(e)}")
            return False
    
    def show_menu(self, title, options):
        """显示菜单并获取用户选择"""
        self.droid.dialogCreateAlert(title)
        self.droid.dialogSetItems(options)
        self.droid.dialogShow()
        response = self.droid.dialogGetResponse().result
        self.droid.dialogDismiss()
        return response['item']
    
    def select_category(self):
        """选择听写类别"""
        categories = ["中文詞語", "中文課文", "英文詞語", "英文課文", "常識詞語"]
        choice = self.show_menu("选择听写类别", categories)
        category = categories[choice]
        
        # 获取该类别下的课程列表
        lessons = [key for key in self.data.keys() if category in key]
        if not lessons:
            self.droid.makeToast("未找到相关课程")
            return None, None
            
        lesson_choice = self.show_menu("选择课程", lessons)
        selected_lesson = lessons[lesson_choice]
        
        return category, selected_lesson
    
    def select_language(self, category):
        """选择语言（针对中文内容）"""
        if category in ["中文詞語", "中文課文", "常識詞語"]:
            languages = ["廣東話", "普通話"]
            choice = self.show_menu("选择语言", languages)
            return languages[choice]
        else:
            return "英语"  # 英文内容默认使用英语
    
    def get_items(self, category, lesson):
        """获取要听写的项目列表"""
        if category in ["中文詞語", "英文詞語", "常識詞語"]:
            # 词语类别，直接返回该课程的词语列表
            return list(self.data[lesson][0].keys())
        else:
            # 课文类别，返回课文内容
            return [item for sublist in self.data[lesson] for item in sublist.keys()]
    
    def speak_text(self, text, language):
        """使用TTS朗读文本"""
        try:
            if language == "廣東話":
                self.droid.ttsSpeak(text, "zh", "HK")
            elif language == "普通話":
                self.droid.ttsSpeak(text, "zh", "CN")
            else:  # 英语
                self.droid.ttsSpeak(text, "en", "US")
            
            # 等待朗读完成
            time.sleep(len(text) * 0.1 + 2)
        except Exception as e:
            self.droid.makeToast(f"朗读失败: {str(e)}")
    
    def run_dictation(self):
        """运行听写程序"""
        if not self.load_data():
            return
            
        category, lesson = self.select_category()
        if not category:
            return
            
        language = self.select_language(category)
        self.current_items = self.get_items(category, lesson)
        self.current_index = 0
        
        if not self.current_items:
            self.droid.makeToast("没有找到听写内容")
            return
        
        self.droid.makeToast(f"开始听写: {lesson} ({language})")
        
        while self.current_index < len(self.current_items):
            current_item = self.current_items[self.current_index]
            
            # 朗读当前项目
            self.speak_text(current_item, language)
            
            # 询问用户操作
            choice = self.show_menu(
                f"项目 {self.current_index + 1}/{len(self.current_items)}", 
                ["重复朗读", "下一个", "退出"]
            )
            
            if choice == 0:  # 重复朗读
                continue
            elif choice == 1:  # 下一个
                self.current_index += 1
            else:  # 退出
                break
        
        self.droid.makeToast("听写完成！")

# 运行程序
if __name__ == "__main__":
    app = DictationApp()
    app.run_dictation()
