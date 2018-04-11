# coding: utf-8
import os
import json
import graphviz as gv
import argparse


class Clazz(object):
    def __init__(self, id):
        self.id = id


class Relation(object):
    def __init__(self, id, source, target, name=None):
        self.id = id
        self.source = source
        self.target = target
        self.name = name or id


class Object(object):
    def __init__(self, id, type, name=None):
        self.id = id
        self.type = type
        self.name = name or id


class RelationInstance(object):
    def __init__(self, id, source, target, type):
        self.id = id
        self.source = source
        self.target = target
        self.type = type


dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def assert_existance(raw_dict, name, prefix):
    if not raw_dict.get(name):
        raise Exception('{0}缺少{1}字段或{1}为空'.format(prefix, name))
    return raw_dict.get(name)


def load_metamodel(metamodel_dict):
    raw_classes = metamodel_dict.get('classes')
    if not raw_classes or not isinstance(raw_classes, list):
        raise Exception('未找到{0}或{0}不为非空数组'.format('classes'))
    raw_relations = metamodel_dict.get('relations')
    if not raw_relations or not isinstance(raw_relations, list):
        raise Exception('未找到{0}或{0}不为非空数组'.format('raw_relations'))
    classes, relations = {}, {}

    for raw_clazz in raw_classes:
        id_ = assert_existance(raw_clazz, 'id', 'metamodel中某class')
        if id_ in classes:
            raise Exception('metamodel中class出现重复的id：{0}'.format(id_))
        classes[id_] = Clazz(**raw_clazz)

    for raw_relation in raw_relations:
        id_ = assert_existance(raw_relation, 'id', 'metamodel中某relation')
        if id_ in relations:
            raise Exception('metamodel中relation出现重复的id：{0}'.format(id_))
        for k in ['source', 'target']:
            end = assert_existance(raw_relation, k, 'metamodel中某relation')
            if end not in classes:
                raise Exception('metamodel中某relation的{0}的类型{1}不存在'.format(k, end))
        relations[id_] = Relation(**raw_relation)
    return classes, relations


def draw_metamodel(classes, relations, problem_name):
    graph = gv.Digraph(format='png')
    for clazz in classes.values():
        graph.node(clazz.id, label=clazz.id, shape='box')
    for relation in relations.values():
        graph.edge(relation.source, relation.target, label=relation.name)
    graph.render('{0}/visualize/{1}/metamodel'.format(dir_path, problem_name))


def load_graph(graph, classes, relations):
    if not graph:
        return {}, {}
    raw_objects = graph.get('objects', [])
    if not raw_objects or not isinstance(raw_objects, list):
        raise Exception('未找到{0}或{0}不为非空数组'.format('objects'))
    raw_relation_instances = graph.get('relations')
    if raw_relation_instances and not isinstance(raw_relation_instances, list):
        raise Exception('{0}格式错误'.format('relations'))
    objects, relation_instances = {}, {}

    for raw_object in raw_objects:
        id_ = assert_existance(raw_object, 'id', 'graph中某object')
        if id_ in objects:
            raise Exception('graph中object出现重复的id：{0}'.format(id_))
        type_ = assert_existance(raw_object, 'type', 'graph中某object')
        if type_ not in classes:
            raise Exception('graph中某object的类型{0}不存在于metamodel中'.format(type_))
        objects[id_] = Object(**raw_object)

    for raw_relation in raw_relation_instances:
        if 'id' in raw_relation:
            raise Exception('relation实例中包含非法的字段：id')
        source = assert_existance(raw_relation, 'source', 'graph中某relation')
        target = assert_existance(raw_relation, 'target', 'graph中某relation')
        if source not in objects:
            raise Exception('graph中某relation的source的对象{0}不存在'.format(source))
        if target not in objects:
            raise Exception('graph中某relation的target的对象{0}不存在'.format(target))
        type_ = assert_existance(raw_relation, 'type', 'graph中某relation')
        if type_ not in relations:
            raise Exception('graph中某relation的类型{0}不存在于metamodel中'.format(type_))
        if objects[source].type != relations[type_].source or \
                        objects[target].type != relations[type_].target:
            raise Exception('graph中某relation的两端与类型不符')
        id_ = '{0}_{1}:{2}'.format(source, target, type_)
        if id_ in relation_instances:
            raise Exception('graph中relation出现重复的id：{0}'.format(id_))
        relation_instances[id_] = RelationInstance(id=id_, **raw_relation)
    return objects, relation_instances


def load_rule(rule_dict, classes, relations):
    raw_lhs = rule_dict.get('lhs')
    if not raw_lhs or not isinstance(raw_lhs, dict):
        raise Exception('未找到{0}或{0}为空'.format('lhs'))
    raw_rhs = rule_dict.get('rhs', {})
    if not isinstance(raw_rhs, dict):
        raise Exception('{0}格式错误'.format('rhs'))
    raw_nacs = rule_dict.get('nacs', [])
    if not isinstance(raw_nacs, list):
        raise Exception('{0}格式错误'.format('nacs'))

    lhs = load_graph(raw_lhs, classes, relations)
    rhs = load_graph(raw_rhs, classes, relations)
    nacs = [load_graph(raw_nac, classes, relations) for raw_nac in raw_nacs]
    return lhs, rhs, nacs


def draw_rule(rule_id, lhs, rhs, nacs, relations, problem_name):
    preserve_color, create_color, delete_color, nac_color = '#0033CC', '#00CC33', '#FF0000', '#666666'

    graph = gv.Digraph(format='png', graph_attr={'label': rule_id, 'labelloc': 'top'}, node_attr={'shape': 'box'})

    # lhs
    for oid, obj in lhs[0].items():
        graph.node(
            obj.id,
            label='<<{0}>>\n{1}:{2}'.format('preserve' if oid in rhs[0] else 'delete', obj.name, obj.type),
            color=(preserve_color if oid in rhs[0] else delete_color),
            fontcolor=(preserve_color if oid in rhs[0] else delete_color))
    for rid, relation in lhs[1].items():
        graph.edge(
            relation.source, relation.target,
            label='<<{0}>>\n{1}'.format('preserve' if rid in rhs[1] else 'delete', relations[relation.type].name),
            color=(preserve_color if rid in rhs[1] else delete_color),
            fontcolor=(preserve_color if rid in rhs[1] else delete_color))

    # nacs
    for idx, nac in enumerate(nacs):
        sub_graph = gv.Digraph(
            name='cluster_nac_{0}'.format(idx),
            graph_attr={'style': 'dotted', 'label': 'nac {0}'.format(idx)})
        for oid, obj in nac[0].items():
            if oid in lhs[0]:
                continue
            sub_graph.node(
                'nac_{0}_{1}'.format(idx, obj.id), label='<<{0}>>\n{1}:{2}'.format('nac', obj.name, obj.type),
                color=nac_color, fontcolor=nac_color)
        for rid, relation in nac[1].items():
            if rid in lhs[1]:
                continue
            get_id = lambda id_: id_ if id_ in lhs[0] else 'nac_{0}_{1}'.format(idx, id_)
            sub_graph.edge(
                get_id(relation.source), get_id(relation.target),
                label='<<{0}>>\n{1}'.format('nac', relations[relation.type].name),
                color=nac_color, fontcolor=nac_color)
        graph.subgraph(sub_graph)

    # rhs
    for oid, obj in rhs[0].items():
        if oid in lhs[0]:
            continue
        graph.node(
            obj.id, label='<<{0}>>\n{1}:{2}'.format('create', obj.name, obj.type),
            color=create_color, fontcolor=create_color)
    for rid, relation in rhs[1].items():
        if rid in lhs[1]:
            continue
        graph.edge(
            relation.source, relation.target,
            label='<<{0}>>\n{1}'.format('create', relations[relation.type].name),
            color=create_color, fontcolor=create_color)

    graph.render('{0}/visualize/{1}/rules/{2}'.format(dir_path, problem_name, rule_id))


def load_goal(goal_dict, classes, relations):
    raw_gf = goal_dict.get('graph', {})
    if not isinstance(raw_gf, dict):
        raise Exception('{0}格式错误'.format('gf'))
    raw_nacs = goal_dict.get('nacs', [])
    if not isinstance(raw_nacs, list):
        raise Exception('{0}格式错误'.format('nacs'))

    gf = load_graph(raw_gf, classes, relations)
    nacs = [load_graph(raw_nac, classes, relations) for raw_nac in raw_nacs]
    return gf, nacs


def draw_goal(gf, nacs, relations, problem_name):
    nac_color = '#666666'

    graph = gv.Digraph(format='png', graph_attr={'label': 'Goal', 'labelloc': 'top'}, node_attr={'shape': 'box'})

    # gf
    for oid, obj in gf[0].items():
        graph.node(
            obj.id,
            label='{0}:{1}'.format(obj.name, obj.type))
    for rid, relation in gf[1].items():
        graph.edge(
            relation.source, relation.target,
            label=relations[relation.type].name)

    # nacs
    for idx, nac in enumerate(nacs):
        sub_graph = gv.Digraph(
            name='cluster_nac_{0}'.format(idx),
            graph_attr={'style': 'dotted', 'label': 'nac {0}'.format(idx)})
        for oid, obj in nac[0].items():
            if oid in gf[0]:
                continue
            sub_graph.node(
                'nac_{0}_{1}'.format(idx, obj.id), label='<<{0}>>\n{1}:{2}'.format('nac', obj.name, obj.type),
                color=nac_color, fontcolor=nac_color)
        for rid, relation in nac[1].items():
            if rid in gf[1]:
                continue
            get_id = lambda id_: id_ if id_ in gf[0] else 'nac_{0}_{1}'.format(idx, id_)
            sub_graph.edge(
                get_id(relation.source), get_id(relation.target),
                label='<<{0}>>\n{1}'.format('nac', relations[relation.type].name),
                color=nac_color, fontcolor=nac_color)
        graph.subgraph(sub_graph)

    graph.render('{0}/visualize/{1}/goal'.format(dir_path, problem_name))


def draw_instance(objects, relation_instances, relations, problem_name, instance_name):
    graph = gv.Digraph(format='png')
    for obj in objects.values():
        graph.node(obj.id, label=obj.id, shape='box')
    for relation in relation_instances.values():
        graph.edge(relation.source, relation.target, relations[relation.type].name)
    graph.render('{0}/visualize/{1}/{2}'.format(dir_path, problem_name, instance_name))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('problem_name', type=str, help='name of the problem directory under examples/')
    parser.add_argument(
        '--instance', type=str,
        help='check and visualize the instance file under examples/{problem_name}/{instance}')
    parser.add_argument(
        '--check_only', action='store_true',
        help='validate the model only, neither dot file nor picture will be generated')
    args = parser.parse_args()
    problem_name = args.problem_name

    with open('{0}/examples/{1}/metamodel.json'.format(dir_path, problem_name)) as metamodel_file:
        # load metamodel
        try:
            metamodel_dict = json.load(metamodel_file)
            classes, relations = load_metamodel(metamodel_dict)
            if not args.check_only:
                draw_metamodel(classes, relations, problem_name)
            print ('Metamodel validation passed.')
        except Exception as ex:
            raise Exception('载入metamodel出错：{0}'.format(ex))

        if args.instance:
            # load instances
            if not args.instance.endswith('.json'):
                raise Exception('载入instance出错：文件格式错误')
            with open('{0}/examples/{1}/{2}'.format(dir_path, problem_name, args.instance)) as instance_file:
                try:
                    instance_dict = json.load(instance_file)
                    if not instance_dict:
                        raise Exception('载入instance出错：实例为空')
                    objs, relas = load_graph(instance_dict, classes, relations)
                    if not args.check_only:
                        draw_instance(objs, relas, relations, problem_name, args.instance[:-5])
                    print ('Instance validation passed.')
                except Exception as ex:
                    raise Exception('载入instance出错：{0}'.format(ex))
        else:
            with open('{0}/examples/{1}/rules.json'.format(dir_path, problem_name)) as rules_file:
                # load rules
                try:
                    rules_arr = json.load(rules_file)
                    rule_ids = []
                    for raw_rule in rules_arr:
                        rule_id = raw_rule.get('id')
                        if not rule_id:
                            raise Exception('rule未包含id字段')
                        if rule_id in rule_ids:
                            raise Exception('重复的rule id: {0}'.format(rule_id))
                        rule_ids.append(rule_id)
                        lhs, rhs, nacs = load_rule(raw_rule, classes, relations)
                        if not args.check_only:
                            draw_rule(rule_id, lhs, rhs, nacs, relations, problem_name)
                    print ('Rules validation passed.')
                except Exception as ex:
                    raise Exception('载入rules出错：{0}'.format(ex))

                with open('{0}/examples/{1}/goal.json'.format(dir_path, problem_name)) as goal_file:
                    # load goal
                    try:
                        goal_dict = json.load(goal_file)
                        gf, nacs = load_goal(goal_dict, classes, relations)
                        if not args.check_only:
                            draw_goal(gf, nacs, relations, problem_name)
                        print ('Goal validation passed.')
                    except Exception as ex:
                        raise Exception('载入goal出错：{0}'.format(ex))
