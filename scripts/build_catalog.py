from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "vue-app" / "public" / "sc2-icons"
OUT = ROOT / "vue-app" / "src" / "data" / "sc2-catalog.json"

# (canonical sc2reader key, TactiX Abbr, English name, Chinese name, kind, race, aliases)
ITEMS = [
    # Protoss buildings
    ("Nexus", "Pbn", "Nexus", "星灵枢纽", "building", "P", []),
    ("Assimilator", "Pba", "Assimilator", "吸纳仓", "building", "P", ["AssimilatorRich"]),
    ("Pylon", "Pbe", "Pylon", "水晶塔", "building", "P", []),
    ("Gateway", "Pbg", "Gateway", "传送门", "building", "P", []),
    ("WarpGate", "Pbgg", "Warp Gate", "变形折跃门", "building", "P", ["WarpGate"]),
    ("Forge", "Pbf", "Forge", "锻炉", "building", "P", []),
    ("CyberneticsCore", "Pby", "Cybernetics Core", "控制芯核", "building", "P", []),
    ("PhotonCannon", "Pbc", "Photon Cannon", "光子炮台", "building", "P", []),
    ("ShieldBattery", "Pbb", "Shield Battery", "护盾充能器", "building", "P", []),
    ("Stargate", "Pvs", "Stargate", "星门", "building", "P", []),
    ("RoboticsFacility", "Pvr", "Robotics Facility", "机械台", "building", "P", []),
    ("TwilightCouncil", "Pvc", "Twilight Council", "光影议会", "building", "P", []),
    ("RoboticsBay", "Pvb", "Robotics Bay", "机械研究所", "building", "P", []),
    ("FleetBeacon", "Pvf", "Fleet Beacon", "舰队航标", "building", "P", []),
    ("TemplarArchive", "Pvt", "Templar Archives", "圣堂武士文献馆", "building", "P", []),
    ("DarkShrine", "Pvd", "Dark Shrine", "黑暗圣坛", "building", "P", []),
    # Protoss units
    ("Probe", "Pbne", "Probe", "探机", "unit", "P", []),
    ("Zealot", "Pbgz", "Zealot", "狂热者", "unit", "P", []),
    ("Stalker", "Pbgs", "Stalker", "追猎者", "unit", "P", []),
    ("Sentry", "Pbge", "Sentry", "机械哨兵", "unit", "P", []),
    ("Adept", "Pbgh", "Adept", "使徒", "unit", "P", []),
    ("HighTemplar", "Pbgt", "High Templar", "高阶圣堂武士", "unit", "P", []),
    ("DarkTemplar", "Pbgd", "Dark Templar", "黑暗圣堂武士", "unit", "P", []),
    ("Archon", "Pbgtt", "Archon", "执政官", "unit", "P", []),
    ("Observer", "Pvrb", "Observer", "侦测器", "unit", "P", ["ObserverSiegeMode"]),
    ("Immortal", "Pvri", "Immortal", "不朽者", "unit", "P", []),
    ("Colossus", "Pvrc", "Colossus", "巨像", "unit", "P", []),
    ("Disruptor", "Pvrd", "Disruptor", "干扰者", "unit", "P", []),
    ("WarpPrism", "Pvra", "Warp Prism", "折跃棱镜", "unit", "P", ["WarpPrismPhasing"]),
    ("Phoenix", "Pvsx", "Phoenix", "凤凰战机", "unit", "P", []),
    ("VoidRay", "Pvsv", "Void Ray", "虚空辉光舰", "unit", "P", []),
    ("Oracle", "Pvse", "Oracle", "先知", "unit", "P", []),
    ("Tempest", "Pvst", "Tempest", "风暴战舰", "unit", "P", []),
    ("Carrier", "Pvsc", "Carrier", "航母", "unit", "P", []),
    ("Interceptor", "Pvsc", "Interceptor", "拦截机", "unit", "P", []),
    ("Mothership", "Pbnm", "Mothership", "母舰", "unit", "P", []),
    # Terran buildings
    ("CommandCenter", "Tbc", "Command Center", "指挥中心", "building", "T", []),
    ("OrbitalCommand", "Tbcb", "Orbital Command", "轨道控制基地", "building", "T", []),
    ("PlanetaryFortress", "Tbcp", "Planetary Fortress", "行星要塞", "building", "T", []),
    ("SupplyDepot", "Tbs", "Supply Depot", "补给站", "building", "T", ["SupplyDepotLowered"]),
    ("Refinery", "Tbr", "Refinery", "精炼厂", "building", "T", ["RefineryRich"]),
    ("Barracks", "Tbb", "Barracks", "兵营", "building", "T", []),
    ("EngineeringBay", "Tbe", "Engineering Bay", "工程站", "building", "T", []),
    ("Bunker", "Tbu", "Bunker", "地堡", "building", "T", []),
    ("SensorTower", "Tbn", "Sensor Tower", "感应塔", "building", "T", []),
    ("MissileTurret", "Tbt", "Missile Turret", "导弹塔", "building", "T", []),
    ("Factory", "Tvf", "Factory", "重工厂", "building", "T", []),
    ("GhostAcademy", "Tvg", "Ghost Academy", "幽灵军校", "building", "T", []),
    ("Starport", "Tvs", "Starport", "星港", "building", "T", []),
    ("Armory", "Tva", "Armory", "军械库", "building", "T", []),
    ("FusionCore", "Tvc", "Fusion Core", "聚变芯体", "building", "T", []),
    ("TechLab", "Tx", "Tech Lab", "科技实验室", "building", "T", ["BarracksTechLab", "FactoryTechLab", "StarportTechLab"]),
    ("Reactor", "Tc", "Reactor", "反应堆挂件", "building", "T", ["BarracksReactor", "FactoryReactor", "StarportReactor"]),
    # Terran units
    ("SCV", "Tbcs", "SCV", "SCV", "unit", "T", []),
    ("MULE", "Tbcbe", "MULE", "矿骡", "unit", "T", []),
    ("Marine", "Tbba", "Marine", "陆战队员", "unit", "T", []),
    ("Marauder", "Tbbd", "Marauder", "劫掠者", "unit", "T", []),
    ("Reaper", "Tbbr", "Reaper", "收割者", "unit", "T", []),
    ("Ghost", "Tbbg", "Ghost", "幽灵", "unit", "T", []),
    ("Nuke", "Tvgn", "Nuke", "核弹", "unit", "T", []),
    ("Hellion", "Tvfe", "Hellion", "恶火", "unit", "T", []),
    ("Hellbat", "Tvfr", "Hellbat", "恶蝠", "unit", "T", ["BattleHellion", "HellionTank"]),
    ("WidowMine", "Tvfd", "Widow Mine", "寡妇雷", "unit", "T", ["WidowMineBurrowed"]),
    ("Cyclone", "Tvfn", "Cyclone", "飓风", "unit", "T", []),
    ("SiegeTank", "Tvfs", "Siege Tank", "攻城坦克", "unit", "T", ["SiegeTankSieged"]),
    ("Thor", "Tvft", "Thor", "雷神", "unit", "T", ["ThorAP"]),
    ("Viking", "Tvsv", "Viking", "维京战机", "unit", "T", ["VikingFighter", "VikingAssault"]),
    ("Medivac", "Tvsd", "Medivac", "医疗运输机", "unit", "T", []),
    ("Liberator", "Tvsn", "Liberator", "解放者", "unit", "T", ["LiberatorAG"]),
    ("Raven", "Tvsr", "Raven", "铁鸦", "unit", "T", []),
    ("Banshee", "Tvse", "Banshee", "女妖", "unit", "T", []),
    ("Battlecruiser", "Tvsb", "Battlecruiser", "战列巡洋舰", "unit", "T", []),
    # Zerg buildings
    ("Hatchery", "Zbh", "Hatchery", "孵化场", "building", "Z", []),
    ("Lair", "Zbhl", "Lair", "虫穴", "building", "Z", []),
    ("Hive", "Zbhlh", "Hive", "主巢", "building", "Z", []),
    ("Extractor", "Zbe", "Extractor", "萃取房", "building", "Z", ["ExtractorRich"]),
    ("SpawningPool", "Zbs", "Spawning Pool", "分裂池", "building", "Z", []),
    ("EvolutionChamber", "Zbv", "Evolution Chamber", "进化腔", "building", "Z", []),
    ("RoachWarren", "Zbr", "Roach Warren", "蟑螂温室", "building", "Z", []),
    ("BanelingNest", "Zbb", "Baneling Nest", "爆虫巢穴", "building", "Z", []),
    ("SpineCrawler", "Zbc", "Spine Crawler", "脊针爬虫", "building", "Z", ["SpineCrawlerUprooted"]),
    ("SporeCrawler", "Zba", "Spore Crawler", "孢子爬虫", "building", "Z", ["SporeCrawlerUprooted"]),
    ("HydraliskDen", "Zvh", "Hydralisk Den", "刺蛇巢", "building", "Z", []),
    ("LurkerDen", "Zvd", "Lurker Den", "潜伏者巢穴", "building", "Z", ["LurkerDenMP"]),
    ("InfestationPit", "Zvi", "Infestation Pit", "感染深渊", "building", "Z", []),
    ("Spire", "Zvs", "Spire", "尖塔", "building", "Z", []),
    ("GreaterSpire", "Zvsg", "Greater Spire", "巨型尖塔", "building", "Z", []),
    ("NydusNetwork", "Zvn", "Nydus Network", "虫道网络", "building", "Z", []),
    ("UltraliskCavern", "Zvu", "Ultralisk Cavern", "雷兽窟", "building", "Z", []),
    # Zerg units
    ("Drone", "Zsd", "Drone", "工蜂", "unit", "Z", ["DroneBurrowed"]),
    ("Overlord", "Zsv", "Overlord", "王虫", "unit", "Z", []),
    ("Queen", "Zbhq", "Queen", "虫后", "unit", "Z", ["QueenBurrowed"]),
    ("Zergling", "Zsz", "Zergling", "跳虫", "unit", "Z", ["ZerglingBurrowed"]),
    ("Baneling", "Zsze", "Baneling", "爆虫", "unit", "Z", ["BanelingBurrowed", "BanelingCocoon"]),
    ("Roach", "Zsr", "Roach", "蟑螂", "unit", "Z", ["RoachBurrowed"]),
    ("Ravager", "Zsrv", "Ravager", "破坏者", "unit", "Z", ["RavagerBurrowed", "RavagerCocoon"]),
    ("Hydralisk", "Zsh", "Hydralisk", "刺蛇", "unit", "Z", ["HydraliskBurrowed"]),
    ("Lurker", "Zshe", "Lurker", "潜伏者", "unit", "Z", ["LurkerBurrowed", "LurkerMP", "LurkerMPBurrowed", "LurkerMPEgg"]),
    ("Infestor", "Zsf", "Infestor", "感染者", "unit", "Z", ["InfestorBurrowed"]),
    ("SwarmHost", "Zsa", "Swarm Host", "虫群宿主", "unit", "Z", ["SwarmHostBurrowed"]),
    ("Ultralisk", "Zsu", "Ultralisk", "雷兽", "unit", "Z", ["UltraliskBurrowed"]),
    ("Mutalisk", "Zst", "Mutalisk", "异龙", "unit", "Z", []),
    ("Corruptor", "Zsc", "Corruptor", "腐化者", "unit", "Z", []),
    ("BroodLord", "Zscb", "Brood Lord", "巢虫领主", "unit", "Z", ["BroodLordCocoon"]),
    ("Viper", "Zse", "Viper", "飞蛇", "unit", "Z", []),
    ("Overseer", "Zsvv", "Overseer", "眼虫", "unit", "Z", ["OverseerSiegeMode", "OverlordCocoon"]),
    ("NydusWorm", "Zvnn", "Nydus Worm", "坑道虫", "unit", "Z", ["NydusCanal"]),
    # Upgrades
    ("WarpGateResearch", "Pbyg", "Warp Gate", "研究折跃门", "upgrade", "P", []),
    ("Charge", "Pvcc", "Charge", "冲锋", "upgrade", "P", []),
    ("BlinkTech", "Pvcb", "Blink", "闪现", "upgrade", "P", []),
    ("ResonatingGlaives", "Pvca", "Resonating Glaives", "共鸣之刃", "upgrade", "P", []),
    ("PsiStormTech", "Pvtt", "Psionic Storm", "灵能风暴", "upgrade", "P", []),
    ("ShadowStride", "Pvdb", "Shadow Stride", "暗影步", "upgrade", "P", []),
    ("GraviticDrive", "Pvbg", "Gravitic Drive", "重力驱动器", "upgrade", "P", []),
    ("GraviticBoosters", "Pvbb", "Gravitic Boosters", "重力加速器", "upgrade", "P", ["ObserverGraviticBooster"]),
    ("ExtendedThermalLance", "Pvbe", "Extended Thermal Lance", "加长热能射线枪", "upgrade", "P", []),
    ("AnionPulseCrystals", "Pvfr", "Anion Pulse-Crystals", "阴离子脉冲水晶", "upgrade", "P", []),
    ("FluxVanes", "Pvff", "Flux Vanes", "熔流旋叶", "upgrade", "P", []),
    ("TectonicDestabilizers", "Pvft", "Tectonic Destabilizers", "构造失稳器", "upgrade", "P", ["TempestGroundAttackUpgrade", "TempestGroundAttackUpgrade (upgrade missing)"]),
    ("Stimpack", "Tbbxt", "Stimpack", "强化剂", "upgrade", "T", []),
    ("ShieldWall", "Tbbxc", "Combat Shield", "防暴盾牌", "upgrade", "T", []),
    ("PunisherGrenades", "Tbbxg", "Concussive Shells", "震撼弹", "upgrade", "T", ["ConcussiveShells"]),
    ("NeosteelArmor", "Tbeb", "Neosteel Armor", "精钢护甲", "upgrade", "T", []),
    ("HiSecAutoTracking", "Tbeh", "Hi-Sec Auto Tracking", "瞬时自动追踪", "upgrade", "T", []),
    ("PersonalCloaking", "Tvgc", "Personal Cloaking", "隐形迷彩", "upgrade", "T", []),
    ("CaduceusReactor", "Tvca", "Caduceus Reactor", "卡度休斯反应堆", "upgrade", "T", []),
    ("MedivacIncreaseSpeedBoost", "Tvca", "Medivac Speed Boost", "医疗运输机加速", "upgrade", "T", []),
    ("AdvancedBallistics", "Tvcn", "Advanced Ballistics", "强化弹道", "upgrade", "T", ["LiberatorAGRangeUpgrade"]),
    ("YamatoCannon", "Tvcr", "Yamato Cannon", "大和炮", "upgrade", "T", []),
    ("BattlecruiserEnableSpecializations", "Tvcr", "Battlecruiser Specializations", "战列巡航舰专精", "upgrade", "T", []),
    ("DrillClaws", "Tvfxc", "Drilling Claws", "钻地之爪", "upgrade", "T", []),
    ("InfernalPreigniter", "Tvfxi", "Infernal Pre-Igniter", "地狱火预燃器", "upgrade", "T", []),
    ("MagFieldAccelerator", "Tvfxr", "Mag-Field Accelerator", "电磁立场加速器", "upgrade", "T", []),
    ("SmartServos", "Tvfxs", "Smart Servos", "智能伺服器", "upgrade", "T", []),
    ("HyperflightRotors", "Tvsxb", "Hyperflight Rotors", "高速旋翼", "upgrade", "T", ["BansheeSpeed"]),
    ("CloakingField", "Tvsxc", "Banshee Cloaking Field", "隐形立场", "upgrade", "T", ["BansheeCloak"]),
    ("InterferenceMatrix", "Tvsxe", "Interference Matrix", "干扰矩阵", "upgrade", "T", []),
    ("MetabolicBoost", "Zbsm", "Metabolic Boost", "代谢加速", "upgrade", "Z", []),
    ("AdrenalGlands", "Zbsa", "Adrenal Glands", "肾上腺体", "upgrade", "Z", []),
    ("CentrifugalHooks", "Zbbc", "Centrifugal Hooks", "环心镰钩", "upgrade", "Z", []),
    ("Burrow", "Zbhb", "Burrow", "潜地", "upgrade", "Z", []),
    ("PneumatizedCarapace", "Zbhp", "Pneumatized Carapace", "充气甲壳", "upgrade", "Z", []),
    ("GlialReconstitution", "Zbrg", "Glial Reconstitution", "神经胶原重组", "upgrade", "Z", []),
    ("TunnelingClaws", "Zbrt", "Tunneling Claws", "掘地之爪", "upgrade", "Z", []),
    ("GroovedSpines", "Zvhg", "Grooved Spines", "深槽脊刺", "upgrade", "Z", []),
    ("MuscularAugments", "Zvhf", "Muscular Augments", "纳米肌肉膨胀", "upgrade", "Z", []),
    ("NeuralParasite", "Zvie", "Neural Parasite", "精神寄生", "upgrade", "Z", []),
    ("InfestorEnergyUpgrade", "Zvie", "Infestor Energy", "感染者能量", "upgrade", "Z", []),
    ("Frenzy", "Zbsa", "Frenzy", "狂怒", "upgrade", "Z", ["Frenzy (upgrade missing)"]),
    ("MicrobialShroud", "Zvic", "Microbial Shroud", "微生物环绕云", "upgrade", "Z", []),
    ("ChitinousPlating", "Zvua", "Chitinous Plating", "进化骨板", "upgrade", "Z", []),
    ("AnabolicSynthesis", "Zvuc", "Anabolic Synthesis", "合成代谢", "upgrade", "Z", []),
    ("AdaptiveTalons", "Zvdd", "Adaptive Talons", "适应之爪", "upgrade", "Z", []),
    ("SeismicSpines", "Zvds", "Seismic Spines", "震地脊刺", "upgrade", "Z", []),
    ("VentralSacs", "Zsvt", "Ventral Sacs", "变异腹囊", "upgrade", "Z", []),
    # Level upgrades share one icon per family.
    ("ProtossGroundWeaponsLevel1", "Pbfg", "Ground Weapons 1", "地面武器 1", "upgrade", "P", []),
    ("ProtossGroundWeaponsLevel2", "Pbfg", "Ground Weapons 2", "地面武器 2", "upgrade", "P", []),
    ("ProtossGroundWeaponsLevel3", "Pbfg", "Ground Weapons 3", "地面武器 3", "upgrade", "P", []),
    ("ProtossGroundArmorsLevel1", "Pbfa", "Ground Armor 1", "地面护甲 1", "upgrade", "P", []),
    ("ProtossGroundArmorsLevel2", "Pbfa", "Ground Armor 2", "地面护甲 2", "upgrade", "P", []),
    ("ProtossGroundArmorsLevel3", "Pbfa", "Ground Armor 3", "地面护甲 3", "upgrade", "P", []),
    ("ProtossPlasmaShieldsLevel1", "Pbfs", "Plasma Shields 1", "护盾 1", "upgrade", "P", []),
    ("ProtossPlasmaShieldsLevel2", "Pbfs", "Plasma Shields 2", "护盾 2", "upgrade", "P", []),
    ("ProtossPlasmaShieldsLevel3", "Pbfs", "Plasma Shields 3", "护盾 3", "upgrade", "P", []),
    ("ProtossAirWeaponsLevel1", "Pbya", "Air Weapons 1", "空中武器 1", "upgrade", "P", []),
    ("ProtossAirWeaponsLevel2", "Pbya", "Air Weapons 2", "空中武器 2", "upgrade", "P", []),
    ("ProtossAirWeaponsLevel3", "Pbya", "Air Weapons 3", "空中武器 3", "upgrade", "P", []),
    ("ProtossAirArmorsLevel1", "Pbye", "Air Armor 1", "空中护甲 1", "upgrade", "P", []),
    ("ProtossAirArmorsLevel2", "Pbye", "Air Armor 2", "空中护甲 2", "upgrade", "P", []),
    ("ProtossAirArmorsLevel3", "Pbye", "Air Armor 3", "空中护甲 3", "upgrade", "P", []),
    ("TerranInfantryWeaponsLevel1", "Tbee", "Infantry Weapons 1", "步兵武器 1", "upgrade", "T", []),
    ("TerranInfantryWeaponsLevel2", "Tbee", "Infantry Weapons 2", "步兵武器 2", "upgrade", "T", []),
    ("TerranInfantryWeaponsLevel3", "Tbee", "Infantry Weapons 3", "步兵武器 3", "upgrade", "T", []),
    ("TerranInfantryArmorsLevel1", "Tbea", "Infantry Armor 1", "步兵护甲 1", "upgrade", "T", []),
    ("TerranInfantryArmorsLevel2", "Tbea", "Infantry Armor 2", "步兵护甲 2", "upgrade", "T", []),
    ("TerranInfantryArmorsLevel3", "Tbea", "Infantry Armor 3", "步兵护甲 3", "upgrade", "T", []),
    ("TerranVehicleWeaponsLevel1", "Tvae", "Vehicle Weapons 1", "载具武器 1", "upgrade", "T", []),
    ("TerranVehicleWeaponsLevel2", "Tvae", "Vehicle Weapons 2", "载具武器 2", "upgrade", "T", []),
    ("TerranVehicleWeaponsLevel3", "Tvae", "Vehicle Weapons 3", "载具武器 3", "upgrade", "T", []),
    ("TerranShipWeaponsLevel1", "Tvas", "Ship Weapons 1", "舰船武器 1", "upgrade", "T", []),
    ("TerranShipWeaponsLevel2", "Tvas", "Ship Weapons 2", "舰船武器 2", "upgrade", "T", []),
    ("TerranShipWeaponsLevel3", "Tvas", "Ship Weapons 3", "舰船武器 3", "upgrade", "T", []),
    ("TerranVehicleAndShipArmorsLevel1", "Tvav", "Vehicle/Ship Armor 1", "载具/舰船护甲 1", "upgrade", "T", []),
    ("TerranVehicleAndShipArmorsLevel2", "Tvav", "Vehicle/Ship Armor 2", "载具/舰船护甲 2", "upgrade", "T", []),
    ("TerranVehicleAndShipArmorsLevel3", "Tvav", "Vehicle/Ship Armor 3", "载具/舰船护甲 3", "upgrade", "T", []),
    ("ZergMeleeWeaponsLevel1", "Zbvm", "Melee Attacks 1", "近战攻击 1", "upgrade", "Z", []),
    ("ZergMeleeWeaponsLevel2", "Zbvm", "Melee Attacks 2", "近战攻击 2", "upgrade", "Z", []),
    ("ZergMeleeWeaponsLevel3", "Zbvm", "Melee Attacks 3", "近战攻击 3", "upgrade", "Z", []),
    ("ZergMissileWeaponsLevel1", "Zbva", "Missile Attacks 1", "远程攻击 1", "upgrade", "Z", []),
    ("ZergMissileWeaponsLevel2", "Zbva", "Missile Attacks 2", "远程攻击 2", "upgrade", "Z", []),
    ("ZergMissileWeaponsLevel3", "Zbva", "Missile Attacks 3", "远程攻击 3", "upgrade", "Z", []),
    ("ZergGroundArmorsLevel1", "Zbvc", "Ground Carapace 1", "地面甲壳 1", "upgrade", "Z", []),
    ("ZergGroundArmorsLevel2", "Zbvc", "Ground Carapace 2", "地面甲壳 2", "upgrade", "Z", []),
    ("ZergGroundArmorsLevel3", "Zbvc", "Ground Carapace 3", "地面甲壳 3", "upgrade", "Z", []),
    ("ZergFlyerWeaponsLevel1", "Zvsa", "Flyer Attacks 1", "空中攻击 1", "upgrade", "Z", []),
    ("ZergFlyerWeaponsLevel2", "Zvsa", "Flyer Attacks 2", "空中攻击 2", "upgrade", "Z", []),
    ("ZergFlyerWeaponsLevel3", "Zvsa", "Flyer Attacks 3", "空中攻击 3", "upgrade", "Z", []),
    ("ZergFlyerArmorsLevel1", "Zvsc", "Flyer Carapace 1", "空中甲壳 1", "upgrade", "Z", []),
    ("ZergFlyerArmorsLevel2", "Zvsc", "Flyer Carapace 2", "空中甲壳 2", "upgrade", "Z", []),
    ("ZergFlyerArmorsLevel3", "Zvsc", "Flyer Carapace 3", "空中甲壳 3", "upgrade", "Z", []),
]


def main() -> None:
    catalog = {}
    missing = []
    for key, abbr, name, name_zh, kind, race, aliases in ITEMS:
        if not (ICON_DIR / f"{abbr}.png").exists():
            missing.append(abbr)
        catalog[key] = {
            "key": key,
            "abbr": abbr,
            "name": name,
            "nameZh": name_zh,
            "kind": kind,
            "race": race,
            "aliases": aliases,
        }

    if missing:
        raise SystemExit(f"missing icons: {sorted(set(missing))}")

    level_dir = ICON_DIR / "level"
    for key, item in catalog.items():
        if item["kind"] != "upgrade":
            continue
        icon_key = key
        if key.startswith("TerranVehicleAndShipArmorsLevel"):
            icon_key = key.replace("TerranVehicleAndShipArmorsLevel", "TerranVehicleArmorsLevel")
        candidate = level_dir / f"{icon_key}.png"
        if candidate.exists():
            item["icon"] = f"level/{icon_key}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(catalog)} catalog entries -> {OUT}")


if __name__ == "__main__":
    main()
