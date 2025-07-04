import config_loader as config
from ui import App

if __name__ == "__main__":
    # 确保配置已加载
    config.load_config()
    
    app = App()
    app.mainloop()
