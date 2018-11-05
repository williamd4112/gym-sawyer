from geometry_msgs.msg import Point, Pose
from moveit_msgs.srv import GetPlanningScene
from moveit_msgs.msg import PlanningScene, PlanningSceneComponents, \
    AllowedCollisionMatrix, AllowedCollisionEntry, CollisionObject
import rospy
from shape_msgs.msg import SolidPrimitive


def add_to_acm(acm, object_name):
    # in python3 compiled version moveit, acm.default_entry_values
    # and acm.entry_values return map object
    new_acm = AllowedCollisionMatrix()
    new_acm.entry_names = acm.entry_names
    entry_values = list(acm.entry_values)
    for entry in entry_values:
        new_entry = AllowedCollisionEntry()
        new_entry.enabled = list(entry.enabled)
        new_acm.entry_values.append(new_entry)
    if object_name not in new_acm.entry_names:
        new_acm.entry_names.append(object_name)
        object_entry = AllowedCollisionEntry()
        for i in range(len(new_acm.entry_values) + 1):
            object_entry.enabled.append(True)
        new_acm.entry_values.append(object_entry)
        for entry in new_acm.entry_values:
            entry.enabled.append(True)
    else:
        index = new_acm.entry_names.index(object_name)
        object_entry = AllowedCollisionEntry()
        for i in range(len(new_acm.entry_values)):
            object_entry.enabled.append(True)
        for entry in new_acm.entry_values:
            entry.enabled[index] = True

    new_acm.default_entry_names = acm.default_entry_names
    new_acm.default_entry_values = list(acm.default_entry_values)

    return new_acm


def remove_from_acm(acm, object_name):
    # in python3 compiled version moveit, acm.default_entry_values
    # and acm.entry_values return map object
    new_acm = AllowedCollisionMatrix()
    new_acm.entry_names = acm.entry_names
    entry_values = list(acm.entry_values)
    for entry in entry_values:
        new_entry = AllowedCollisionEntry()
        new_entry.enabled = list(entry.enabled)
        new_acm.entry_values.append(new_entry)
    if object_name not in new_acm.entry_names:
        new_acm.entry_names.append(object_name)
        object_entry = AllowedCollisionEntry()
        for i in range(len(new_acm.entry_values) + 1):
            object_entry.enabled.append(False)
        new_acm.entry_values.append(object_entry)
        for entry in new_acm.entry_values:
            entry.enabled.append(False)
    else:
        index = new_acm.entry_names.index(object_name)
        for i in range(len(new_acm.entry_names)):
            new_acm.entry_values[index].enabled[i] = False
        for entry in new_acm.entry_values:
            entry.enabled[index] = False

    new_acm.default_entry_names = acm.default_entry_names
    new_acm.default_entry_values = list(acm.default_entry_values)

    return new_acm


class MoveitPlanningSceneController(object):
    def __init__(self,
                 moveit_frame):
        self.planning_scene_pub = rospy.Publisher('/planning_scene', PlanningScene, queue_size=10)

        rospy.wait_for_service('/get_planning_scene', 10.0)
        self.get_planning_scene = rospy.ServiceProxy('/get_planning_scene', GetPlanningScene)

        self.moveit_frame = moveit_frame

    def add_object_to_acm(self, object_name):
        req = PlanningSceneComponents(
            components=(PlanningSceneComponents.ALLOWED_COLLISION_MATRIX |
                        PlanningSceneComponents.SCENE_SETTINGS))
        res = self.get_planning_scene(req)
        acm = res.scene.allowed_collision_matrix
        planning_scene_diff = PlanningScene(is_diff=True)

        acm = add_to_acm(acm, object_name)

        planning_scene_diff.allowed_collision_matrix = acm

        self.planning_scene_pub.publish(planning_scene_diff)
        rospy.sleep(2)

    def get_acm(self):
        req = PlanningSceneComponents(
            components=(PlanningSceneComponents.ALLOWED_COLLISION_MATRIX |
                        PlanningSceneComponents.SCENE_SETTINGS))
        res = self.get_planning_scene(req)
        acm = res.scene.allowed_collision_matrix

        return acm

    def remove_object_from_acm(self, object_name):
        req = PlanningSceneComponents(
            components=(PlanningSceneComponents.ALLOWED_COLLISION_MATRIX |
                        PlanningSceneComponents.SCENE_SETTINGS))
        res = self.get_planning_scene(req)
        acm = res.scene.allowed_collision_matrix
        planning_scene_diff = PlanningScene()
        planning_scene_diff.is_diff = True

        acm = remove_from_acm(acm, object_name)

        planning_scene_diff.allowed_collision_matrix = acm
        self.planning_scene_pub.publish(planning_scene_diff)

    def test_add_collision_object(self):
        planning_scene_diff = PlanningScene(is_diff=True)

        rospy.sleep(1)
        pose_stamped_block = Pose()
        # pose_stamped_block.header.frame_id = self.moveit_frame
        pos = Point(0.6, 0., 0.03)
        pos.z += 0.03
        pose_stamped_block.position = pos

        primitive = SolidPrimitive()
        primitive.type = primitive.BOX
        primitive.dimensions = [0.045, 0.045, 0.06]

        test_block = CollisionObject()
        test_block.operation = CollisionObject.ADD
        test_block.primitive_poses.append(pose_stamped_block)
        test_block.primitives.append(primitive)

        planning_scene_diff.world.collision_objects.append(test_block)
        self.planning_scene_pub.publish(planning_scene_diff)
        rospy.sleep(2)
