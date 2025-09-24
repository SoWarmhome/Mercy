import requests
import json
import androidhelper
import time
import sys

class DictationApp:
    def __init__(self):
        try:
            self.droid = androidhelper.Android()
            self.data_url = "https://raw.githubusercontent.com/SoWarmhome/Mercy/main/Dictation/Dictation.json"
            self.data = None
            self.current_items = []
            self.current_index = 0
            print("应用程序初始化成功")
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            self.show_error(f"初始化失败: {str(e)}")
        
    def show_error(self, message):
        """显示错误信息"""
        try:
            self.droid.dialogCreateAlert("错误", message)
            self.droid.dialogSetPositiveButtonText("确定")
            self.droid.dialogShow()
            self.droid.dialogGetResponse()
        except:
            print(message)
    
    def show_message(self, title, message):
        """显示消息"""
        try:
            self.droid.dialogCreateAlert(title, message)
            self.droid.dialogSetPositiveButtonText("确定")
            self.droid.dialogShow()
            self.droid.dialogGetResponse()
        except Exception as e:
            print(f"{title}: {message}")
    
    def load_data(self):
        """从GitHub加载数据"""
        try:
            print("开始加载数据...")
            self.droid.makeToast("正在加载数据...")
            
            # 设置超时时间
            response = requests.get(self.data_url, timeout=30)
            response.encoding = 'utf-8'
            self.data = json.loads(response.text)
            print("数据加载成功")
            return True
        except requests.exceptions.Timeout:
            error_msg = "网络请求超时，请检查网络连接"
            print(error_msg)
            self.show_error(error_msg)
            return False
        except requests.exceptions.ConnectionError:
            error_msg = "网络连接错误，请检查网络设置"
            print(error_msg)
            self.show_error(error_msg)
            return False
        except Exception as e:
            error_msg = f"数据加载失败: {str(e)}"
            print(error_msg)
            self.show_error(error_msg)
            return False
    
    def show_menu(self, title, options):
        """显示菜单并获取用户选择"""
        try:
            self.droid.dialogCreateAlert(title)
            self.droid.dialogSetItems(options)
            self.droid.dialogShow()
            response = self.droid.dialogGetResponse().result
            self.droid.dialogDismiss()
            return response['item']
        except Exception as e:
            print(f"菜单显示错误: {str(e)}")
            return 0
    
    def select_category(self):
        """选择听写类别"""
        try:
            categories = ["中文詞語", "中文課文", "英文詞語", "英文課文", "常識詞語"]
            choice = self.show_menu("选择听写类别", categories)
            category = categories[choice]
            print(f"选择的类别: {category}")
            
            # 获取该类别下的课程列表
            lessons = [key for key in self.data.keys() if category in key and len(key) > len(category)]
            if not lessons:
                lessons = [key for key in self.data.keys() if category in key]
            
            if not lessons:
                self.show_message("提示", "未找到相关课程")
                return None, None
                
            lesson_choice = self.show_menu("选择课程", lessons)
            selected_lesson = lessons[lesson_choice]
            print(f"选择的课程: {selected_lesson}")
            
            return category, selected_lesson
        except Exception as e:
            print(f"选择类别错误: {str(e)}")
            return None, None
    
    def select_language(self, category):
        """选择语言（针对中文内容）"""
        try:
            if category in ["中文詞語", "中文課文", "常識詞語"]:
                languages = ["廣東話", "普通話"]
                choice = self.show_menu("选择语言", languages)
                selected_language = languages[choice]
                print(f"选择的语言: {selected_language}")
                return selected_language
            else:
                return "英语"  # 英文内容默认使用英语
        except Exception as e:
            print(f"选择语言错误: {str(e)}")
            return "普通話"
    
    def get_items(self, category, lesson):
        """获取要听写的项目列表"""
        try:
            print(f"获取项目: {category} - {lesson}")
            
            if lesson not in self.data:
                self.show_message("错误", f"未找到课程数据: {lesson}")
                return []
            
            lesson_data = self.data[lesson]
            
            if category in ["中文詞語", "英文詞語", "常識詞語"]:
                # 词语类别，直接返回该课程的词语列表
                if isinstance(lesson_data, list) and len(lesson_data) > 0:
                    return list(lesson_data[0].keys())
                else:
                    return list(lesson_data.keys())
            else:
                # 课文类别，返回课文内容
                items = []
                for item in lesson_data:
                    if isinstance(item, dict):
                        items.extend(item.keys())
                return items
        except Exception as e:
            print(f"获取项目错误: {str(e)}")
            self.show_error(f"获取项目失败: {str(e)}")
            return []
    
    def speak_text(self, text, language):
        """使用TTS朗读文本"""
        try:
            print(f"朗读: {text} ({language})")
            
            # 清理文本中的标点符号
            clean_text = text.replace('"', '').replace("'", "")
            
            if language == "廣東話":
                self.droid.ttsSpeak(clean_text, "zh", "HK")
            elif language == "普通話":
                self.droid.ttsSpeak(clean_text, "zh", "CN")
            else:  # 英语
                self.droid.ttsSpeak(clean_text, "en", "US")
            
            # 根据文本长度计算等待时间
            wait_time = max(len(clean_text) * 0.15, 2)
            print(f"等待 {wait_time} 秒")
            time.sleep(wait_time)
            
        except Exception as e:
            error_msg = f"朗读失败: {str(e)}"
            print(error_msg)
            self.droid.makeToast(error_msg)
    
    def run_dictation_session(self, category, lesson, language):
        """运行听写会话"""
        self.current_items = self.get_items(category, lesson)
        self.current_index = 0
        
        if not self.current_items:
            self.show_message("提示", "没有找到听写内容")
            return False
        
        total_items = len(self.current_items)
        self.droid.makeToast(f"开始听写: {total_items} 个项目")
        
        while self.current_index < total_items:
            current_item = self.current_items[self.current_index]
            
            # 朗读当前项目
            self.speak_text(current_item, language)
            
            # 询问用户操作
            choice = self.show_menu(
                f"{current_item} ({self.current_index + 1}/{total_items})", 
                ["重复朗读", "下一个", "退出听写"]
            )
            
            if choice == 0:  # 重复朗读
                continue
            elif choice == 1:  # 下一个
                self.current_index += 1
            else:  # 退出
                break
        
        self.show_message("完成", "听写完成！")
        return True
    
    def main_menu(self):
        """主菜单"""
        while True:
            try:
                options = ["开始听写", "测试TTS", "退出程序"]
                choice = self.show_menu("主菜单", options)
                
                if choice == 0:  # 开始听写
                    if not self.load_data():
                        continue
                        
                    category, lesson = self.select_category()
                    if not category:
                        continue
                    
                    language = self.select_language(category)
                    self.run_dictation_session(category, lesson, language)
                    
                elif choice == 1:  # 测试TTS
                    self.test_tts()
                    
                else:  # 退出程序
                    self.show_message("再见", "谢谢使用听写程序！")
                    break
                    
            except Exception as e:
                print(f"主菜单错误: {str(e)}")
                self.show_error(f"程序错误: {str(e)}")
                break
    
    def test_tts(self):
        """测试TTS功能"""
        try:
            test_texts = {
                "普通話": "这是一段普通话测试",
                "廣東話": "這是一段廣東話測試", 
                "英语": "This is an English test"
            }
            
            for lang, text in test_texts.items():
                self.show_message("TTS测试", f"即将播放: {text}")
                self.speak_text(text, lang)
                
        except Exception as e:
            self.show_error(f"TTS测试失败: {str(e)}")

# 主程序
if __name__ == "__main__":
    print("程序开始运行...")
    
    try:
        app = DictationApp()
        print("应用程序创建成功，进入主菜单...")
        app.main_menu()
    except Exception as e:
        print(f"程序运行错误: {str(e)}")
        # 显示错误信息
        try:
            droid = androidhelper.Android()
            droid.dialogCreateAlert("程序错误", str(e))
            droid.dialogSetPositiveButtonText("确定")
            droid.dialogShow()
            droid.dialogGetResponse()
        except:
            pass
    
    print("程序结束")
    # 等待用户按键退出
    input("[QPython] Press enter to exit ...")
