# AA18_Project_Bootstrap
算分2018小班课赵海燕老师班课程项目

## 项目结构
- `examlpes`：问题集合
  - `sokoban_game`：推箱子游戏示例
    - `metamodel.json`：问题的元模型（即问题的静态描述）
    - `rules.json`：问题的规则（即问题的动态描述）
    - `goal.json`：问题的目标
    - `instances`：问题的实例目录
      - `trivial.json`：最简单的推箱子游戏实例
- `utils`：工具集合
  - `check_and_visualize.py`：模型校验和可视化工具

## Quick Start
1. 安装[Python](https://www.python.org/)

   - 模型校验工具是用Python实现的。项目不限制编程语言，但是由于Python在数据处理和算法上的优势，也鼓励大家尝试使用Python完成项目。（Python2、Python3皆可）

2. 安装[graphviz](https://www.graphviz.org/)工具

   - graphviz是一款开源、跨平台的图渲染工具，可以讲制定格式的文件渲染成多种图片的形式

3. 通过PIP安装graphviz依赖

   - 为了能够通过Python调用graphviz，需要先安装Python的graphviz包。安装Python后在终端输入`pip install graphviz`即可

4. 校验工具使用

   - 在项目根目录下输入

     > python utils/check_and_visualize.py sokoban_game

     即会校验推箱子游戏下的`metamodel.json`、`rules.json`、`goal.json`的合法性，同时在项目根目录下的`visualize/sokoban_game`目录下生成对应的图片

   - 输入

     > python utils/check_and_visualize.py sokoban_game --instance instances/trivial.json

     会校验指定实例（`instances/trivial.json`）的合法性，同时在`visualize/sokoban_game`的对应位置生成图片

   - 如果携带参数`--check_only`将会只进行校验，不生成图片

## 模型格式说明

模型包含`metamodel.json`、`rules.json`、`goal.json`以及任意文件名的json格式实例模型

### metamodel.json

一个json对象，其中包含

- `classes`：json数组，包含问题中所有的类，每一个类中包含
  - `id`：必须，不与其他类id重复，类的唯一标识
- `relations`：json数组，包含问题中所有的关系，每一个关系中包含
  - `id`：必须，不与其他关系id重复，关系的唯一标识
  - `source`：必须，为某一类的id，表示关系的源端
  - `target`：必须，为某一类的id，表示关系的目标端
  - `name`：可选，关系的名称，用于展示，如不包含该字段，将用id字段展示

### rules.json

所有的规则组成的json数组，每一个规则包含

- `id`：必须，不与其他规则id重复，规则的唯一标识
- `lhs`：必须，规则的左部（用于匹配），包含一个[对象图](#obj_diagram)
- `rhs`：必须，规则的右部（用于替换左部），包含一个[对象图](#obj_diagram)
- `nacs`：可选，规则的negative application conditions（用于限制规则的适用条件，如果任意一个nac被匹配，则无法apply该rule），包含一个nac的json数组，nac为[对象图](#obj_diagram)的形式
  - `lhs`、`rhs`、`nac`中的对象id只表示他们之间的点（对象）映射关系，**并不具有实际含义**。在与某一实例图匹配的时候，只需考虑类和关系是否匹配
  - `lhs`和`rhs`、`lhs`和`nac`中相同id的对象表示为同一个对象（“会被保留的对象”），只出现于`lhs`的对象为“会被删除的对象”，只出现于`rhs`的对象为“将要新增的对象”
  - 由morphism的定义可知，一旦确定点（对象）的映射关系，边（关系实例）的映射关系亦可确定，即两侧源、目标和类型均相同的关系实例被视为是identical的，若在另一侧找不到对应的关系实例，则被视为是新增/删除的

### goal.json

目标的json对象，包含

- `graph`：可选，满足目标所需要匹配的[对象图](#obj_diagram)
- `nacs`：可选，目标的negative application conditions（如果任意一个nac被匹配，则视为没有满足目标）
  - `graph`与`nacs`不应同时为空，否则goal将没有意义
  - 与规则类似，`graph`和`nac`中的对象id没有实际含义，只表示`graph`与`nac`之间的映射关系

### 实例模型

一个[对象图](#obj_diagram)

### <a name="obj_diagram">对象图</a>

一个json对象，包含

- `objects`：必须，json数组，包含对象图中所有的对象，每一个对象包含
  - `id`：必须，不与其他对象id重复，对象的唯一标识
  - `type`：必须，为metamodel中某一个类的id，对象的类型
  - `name`：可选，对象的别名，用于展示，如不包含该字段，将用id字段展示
- `relations`：可选，json数组，包含对象图中所有的关系实例，每一个关系实例包含
  - `type`：必须，为metamodel中某一个关系的id，关系实例的类型
  - `source`：必须，为某一对象的id，表示关系的源端
  - `target`：必须，为某一对象的id，表示关系的目标端
    - 关系实例**不能**包含id，一个关系实例应该是由上述三个字段唯一确定的

## 项目要求

1. 实现Graph Transformation和基本的搜索策略（DFS/BFS），使得对于任何给定的问题模型和问题实例，可以通过图变换得到一个满足目标的实例，并能判断无解的情况
2. 采用前述模型来描述某一个问题，问题的类型不限，但应该对于搜索具有一定的复杂性，给出问题的模型，以及若干复杂程度不等的实例
3. 尝试给出**问题无关**的搜索优化策略，使得对于不同的问题，都可以在一定程度上减少搜索的时间（或空间）