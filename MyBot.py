import hlt
import logging
from collections import OrderedDict
game = hlt.Game("Settler V9")
logging.info("Starting LogicBot")
turn_number = 0

while True:
    game_map = game.update_map()
    command_queue = []
    targeted_planets = []
    
    for ship in game_map.get_me().all_ships():
        shipid = ship.id

        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
        closest_team_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned() and entities_by_distance[distance][0] in team_planets]

        team_ships = game_map.get_me().all_ships()

        if ship == team_ships[0] and len(team_ships) >= 3:
            assasin_ship = ship
        
        team_planets = []
        for planet in game_map.all_planets():
            if planet.owner == game_map.get_me():
                team_planets.append(planet)

        team_large_planets = []
        for planet in team_planets:
            if planet.health >= 2300:
               team_large_planets.append(planet)

        largest_planet_sizes = []
        for planet in game_map.all_planets():
            largest_planet_sizes.append(planet.health)

        weakest_planets = []
        for planet in game_map.all_planets():
            if planet.health <= 600:
                weakest_planets.append(planet)

        largest_planet_health = max(largest_planet_sizes)
            
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
        closest_enemy_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned() and entities_by_distance[distance][0] not in team_planets]

        vunrable_enemy_planets = []
        for planet in closest_enemy_planets:
            if len(planet.all_docked_ships()) == 1:
                vunrable_enemy_planets.append(planet)

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            if ship.planet.health <= 600:
                navigate_command = ship.undock()

                if navigate_command:
                    command_queue.append(navigate_command)
            else:
                continue
            
        elif len(closest_enemy_ships) == 1:
            target_ship = closest_enemy_ships[0]
            navigate_command = ship.navigate(
                        ship.closest_point_to(target_ship),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)

            if navigate_command:
                command_queue.append(navigate_command)

        elif turn_number <= 40 and len(team_planets) <= 3 and len(closest_team_planets) > 1 and len(game_map.all_players()) == 4:
            if ship.can_dock(closest_team_planets[0]):
                command_queue.append(ship.dock(closest_team_planets[0]))
            elif ship.can_dock(closest_team_planets[0]) == False and len(closest_empty_planets) > 0:
                target_planet = closest_empty_planets[0]
                if target_planet in weakest_planets:
                    if len(closest_enemy_ships) > 0:
                        target_ship = closest_enemy_ships[0]
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(target_ship),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)
            elif ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_planet),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)

        elif ship == assasin_ship:
            if len(vunrable_enemy_planets) > 0:
                target_ship = vunrable_enemy_planets[0].all_docked_ships()[0]
                navigate_command = assasin_ship.navigate(
                            assasin_ship.closest_point_to(target_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)

            elif len(closest_enemy_ships) > 0:
                target_ship = closest_enemy_ships[0]
                navigate_command = assasin_ship.navigate(
                            assasin_ship.closest_point_to(target_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)
        
        # If there are any empty planets, let's try to mine!
        elif turn_number <= 5 and len(closest_empty_planets) >= 3:
            target_planet = closest_empty_planets[0]
            if target_planet in targeted_planets:
                target_planet = closest_empty_planets[1]
            if target_planet in targeted_planets:
                target_planet = closest_empty_planets[2]

            if ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_planet),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)
                    targeted_planets.append(target_planet)

        elif len(closest_enemy_planets) > 0 and int(closest_enemy_planets[0].calculate_distance_between(ship)) <= 30 and len(closest_enemy_planets[0].all_docked_ships()) == 1:
            target_ship = closest_enemy_planets[0].all_docked_ships()[0]
            navigate_command = ship.navigate(
                        ship.closest_point_to(target_ship),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)

            if navigate_command:
                command_queue.append(navigate_command)

        elif largest_planet_health >= 2300 and len(team_planets) >= 5 and len(team_large_planets) > 0 and int(team_large_planets[0].calculate_distance_between(ship)) <= 60 and team_large_planets[0].is_full() == False and ship.can_dock(team_large_planets[0]):
            navigate_command = ship.dock(team_large_planets[0])

            if navigate_command:
                command_queue.append(navigate_command)

        elif len(game_map.all_players()) == 4 and len(team_planets) / len(game_map.all_planets()) >= 0.45:
            if len(closest_enemy_ships) > 0:
                target_ship = closest_enemy_ships[0]
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)
            
        elif len(closest_empty_planets) >= 4:
            target_planet = closest_empty_planets[0]
            if target_planet in weakest_planets:
                target_planet = closest_empty_planets[1]
            if target_planet in weakest_planets:
                target_planet = closest_empty_planets[2]
            if target_planet in weakest_planets:
                target_planet = closest_empty_planets[3]
                
            if ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_planet),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)

        elif len(closest_empty_planets) > 0:
            target_planet = closest_empty_planets[0]
            if target_planet in weakest_planets:
                if len(closest_enemy_ships) > 0:
                    target_ship = closest_enemy_ships[0]
                    navigate_command = ship.navigate(
                                ship.closest_point_to(target_ship),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)

                    if navigate_command:
                        command_queue.append(navigate_command)
            
            elif ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
            else:
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_planet),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)

        # FIND SHIP TO ATTACK!
        else:
            
            try:
                first_enemy_planet_status = closest_enemy_planets[0].is_full()
            except IndexError:
                first_enemy_planet_status = None
                
            if first_enemy_planet_status == True:
                navigate_command = ship.thrust(
                    hlt.constants.MAX_SPEED,
                    ship.calculate_angle_between(closest_enemy_planets[0]))

                if navigate_command:
                    command_queue.append(navigate_command)
        
            elif len(closest_enemy_ships) > 0:
                target_ship = closest_enemy_ships[0]
                navigate_command = ship.navigate(
                            ship.closest_point_to(target_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                if navigate_command:
                    command_queue.append(navigate_command)

    game.send_command_queue(command_queue)
    # TURN END
    turn_number += 1
    
# GAME END
