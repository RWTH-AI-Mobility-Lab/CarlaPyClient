import carla

client = carla.Client('localhost', 2000)
client.set_timeout(5.0)

blueprints = client.get_world().get_blueprint_library().filter('vehicle')
for blueprint in blueprints:
    print(blueprint.id)