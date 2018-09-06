from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from info import create_app,db


# 通过指定的配置名字创建对应配置的app
# create_app类似于工厂方法
app = create_app("development")
# 创建一个flask_script对象托管app,使其支持命令行运行
manager = Manager(app)
# 数据库迁移
migrate = Migrate(app,db)
# 添加迁移命令
manager.add_command("db",MigrateCommand)


if __name__ == "__main__":
    manager.run()