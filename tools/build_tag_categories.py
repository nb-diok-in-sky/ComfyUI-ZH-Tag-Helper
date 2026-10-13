# Step 2 of the word list build: web/tag_categories.json, used by the autocomplete and the 提示词分类 panels.
# Every tag of tools/build/danbooru_tags_zh.csv (run build_zh_tags.py first) sorted into 大类/子类
# (layout borrowed from WeiLin-Comfyui-Tools, its word list is not used).
# General tags, first match wins: R18 words -> keyword RULES -> Danbooru "Tag group:" wiki sections
# (tools/sources/danbooru_groups, from fetch_sources.py) -> 其他/未分类.
# Characters are grouped by series, copyrights go to 作品.
# 违禁词 keep their place and Chinese; the marker build_zh_tags.py put on the alias stays visible.
# Usage: python tools/build_tag_categories.py
import collections
import csv
import json
import os
import re

TOOLS = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(TOOLS, "build/danbooru_tags_zh.csv")
OUT = os.path.join(os.path.dirname(TOOLS), "web/tag_categories.json")
GROUPS = os.path.join(TOOLS, "sources/danbooru_groups")

# Same markers as build_zh_tags.py.
BAN = "🚫违禁词·"
WARN = "⚠违禁词·仅全年龄·"
HAN = re.compile(r"[一-鿿]")
KANA = re.compile(r"[ぁ-ヿ]")
MAX_ALIASES = 12

ORDER = {
    "人物": ["人数·性别", "身份·职业", "种族·非人", "年龄", "身材", "皮肤", "发型", "发色", "头发其他", "面部", "眼睛", "瞳孔",
             "眉毛·睫毛", "嘴巴·牙齿·舌头", "耳朵", "妆容·纹身", "胸部", "臀部", "手·手臂", "腿·脚", "身体其他部位", "翅膀·尾巴·角"],
    "服饰": ["风格·时尚", "制服·职业装", "传统服饰", "泳装·紧身衣", "内衣", "连衣裙", "上衣", "外套·披风", "裙子", "裤子",
             "袜子·腿饰", "鞋子", "手套", "袖子", "领口·领带·颈饰", "帽子·头盔", "发饰", "眼镜·面具", "首饰·饰品", "盔甲",
             "花纹·材质", "衣着状态"],
    "表情动作": ["表情", "视线", "基础姿势", "手臂动作", "手部动作", "手势", "拿着东西", "腿部动作", "多人互动", "其他动作"],
    "镜头": ["景别", "角度", "构图", "焦点"],
    "画面": ["画质·元数据", "艺术风格", "媒介·格式", "光照", "颜色", "背景", "特效", "文字·符号"],
    "环境": ["季节·节日", "天气·时间", "天空", "水·冰·火", "植物·花"],
    "场景": ["室内", "户外·自然", "户外·城市", "建筑", "家具·门窗", "现实地点"],
    "物品": ["武器", "食物·饮料", "动物", "神话生物", "交通工具", "乐器·音乐", "电子设备", "运动·游戏", "其他物品"],
    "R18": ["裸露", "走光·偷窥", "性器官", "性行为", "体位", "体液", "性表情", "色情服装", "BDSM·束缚", "情趣用品", "性癖·其他"],
    "角色": [],
    "作品": ["全部作品"],
    "其他": ["网络梗", "作品相关", "未分类"],
}

# ---------- R18 ----------
R18_SUB = [
    ("体位", r"missionary|cowgirl_position|doggystyle|mating_press|standing_sex|suspended_congress|^spooning$|full_nelson|amazon_position|^69$|piledriver_\(sex\)|prone_bone|sex_from_behind|upright_straddle|reverse_suspended|folded_sex|girl_on_top|boy_on_top|reverse_cowgirl"),
    ("性表情", r"ahegao|torogao|fucked_silly|naughty_face|^aroused$|^afterglow$"),
    ("体液", r"(^|_)cum($|_)|cumdrip|pussy_juice|precum|lactation|breast_milk|smegma|squirting|female_ejaculation|bukkake|^facial$|creampie|after_sex|ejaculation|semen|urine|peeing|(^|_)pee($|_)|suggestive_fluid"),
    ("BDSM·束缚", r"bdsm|bondage|(^|_)bound(_|$)|restrained|shibari|(^|_)gag(_|$)|gagged|ballgag|bit_gag|spreader_bar|tied_up|^chained|shackles|handcuffs|pillory|dominatrix|femdom|(^|_)slave|(^|_)whip($|_)|whipping|riding_crop|torture|hogtie|frogtie|box_tie|wooden_horse|nipple_clamps|gimp_"),
    ("情趣用品", r"dildo|vibrator|sex_toy|butt_plug|anal_beads|condom|tenga|onahole|hitachi_magic_wand|strap-on|fleshlight|sex_machine|aphrodisiac|aneros|anal_tail|yes-no_pillow"),
    ("色情服装", r"crotchless|cupless|nippleless|pasties|maebari|reverse_bunnysuit|reverse_outfit|sling_bikini|microkini|slingshot_swimsuit|see-through_(panties|bra)|pussy_cutout|anus_cutout|breastless|nipple_cutout|crotch_cutout|anal_ball_wear|chastity"),
    ("走光·偷窥", r"upskirt|pantyshot|downblouse|downpants|panty_peek|voyeur|peeping|exhibitionism|public_(nudity|indecency|use|sex)|flashing|wardrobe_malfunction|nip_slip|nipple_slip|areola_slip|panties_aside|panty_pull|skirt_lift|clothes_lift|shirt_lift|dress_lift|bra_lift|lifting_own_clothes|^presenting|_exposure$"),
    ("性器官", r"penis|pussy|vagina|vulva|labia|clitoris|testicles|scrotum|foreskin|glans|erection|nipples?($|_)|areola|(^|_)anus|pubic_hair|female_pubic|male_pubic|uterus|cervix|womb|cameltoe|(^|_)bulge|cleft_of_venus|perineum|urethra|^ovum$|sperm_cell"),
    ("裸露", r"(^|_)nude|naked(?!_choke)|topless|bottomless|breasts_out|undressing|no_panties|no_bra|nudity|undressed|stripping|striptease"),
    ("性行为", r"(^|_)sex($|_)|fellatio|cunnilingus|irrumatio|paizuri|handjob|footjob|thighjob|buttjob|masturbation|fingering|fisting|rimjob|deepthroat|penetration|insertion|groping|molestation|tribadism|frottage|(^|_)rape($|_)|^raped|gangbang|threesome|orgy|group_sex|^hetero$|yaoi|futanari|tentacle_sex|breast_sucking|nipple_(tweak|play|licking|suck)|licking_(penis|nipple|pussy|anus|testicle)|(^|_)oral($|_)|^69$|(^|_)anal($|_)|vaginal|orgasm|impregnation|fertilization|incest|netorare|(^|_)ntr($|_)|prostitution|x-ray|cross-section|internal_cumshot|breast_grab|ass_grab|crotch_grab|grabbing_(another's|own)_(breast|ass)|pov_crotch|imminent_(rape|sex|penetration|fellatio|anal|vaginal|cunnilingus|paizuri)|shimaidon|just_the_tip|^plap$|uncommon_stimulation|interracial|interspecies|pokephilia|kodomo_doushi"),
    ("性癖·其他", r"hypnosis|instant_loss|corruption|pornography|^abuse$|self-harm|(^|_)gaping|sexual_|foreplay|in_heat|aroused_nosebleed|eargasm|arousal|shoejob|kupaa|ero_guro|prolapse|wedgie|drugged|^virgin$|^nudist|torso_flash|stripper|_leash$|strip_game|pubic_|testicle|half-erect|oyakodon|lolidom|lolicon|clitoral|(^|_)raped?($|_)|breasts_on_tray|pregnancy_test|implied_pregnancy|accidental_pervert"),
]
R18_WORDS = re.compile("|".join(p for _, p in R18_SUB))
R18_SUB = [(n, re.compile(p)) for n, p in R18_SUB]

# ---------- keyword rules (general tags) ----------
COLORS = ("aqua|black|blonde|blue|brown|green|grey|gray|orange|pink|purple|red|white|yellow|silver|gold|light_blue|dark_blue|"
          "light_brown|light_green|light_purple|dark_green|dark_red|lavender|beige|multicolored|two-tone|gradient|rainbow|streaked|"
          "colored_inner|split-color|platinum_blonde|strawberry_blonde|dark_skinned|tan|pale|navy_blue|teal|maroon|cyan|magenta|violet")
ANIMALS = ("cat|dog|fox|wolf|rabbit|bunny|bear|mouse|tiger|lion|cow|horse|pig|sheep|goat|deer|raccoon|squirrel|bird|fish|shark|snake|"
           "dragon|frog|bat|monkey|panda|penguin|owl|chicken|duck|crow|eagle|hamster|ferret|otter|seal|whale|dolphin|octopus|"
           "butterfly|bee|spider|lizard|turtle|crab|hedgehog|leopard|cheetah|jaguar|hyena|kitsune|tanuki|weasel|elephant|giraffe|zebra|"
           "kangaroo|koala|sloth|alpaca|llama|camel|boar|ox|bull|reindeer|moose|lynx|ocelot|serval|caracal|puppy|kitten")
RULES = [
    # 其他
    ("其他", "网络梗", r"_\(meme\)$|^meme$"),
    ("画面", "画质·元数据", r"^\d{4}$|^(19|20)\d0s$|absurdres|highres|lowres|commentary|translat|_request$|^bad_|_artifacts$|^jpeg|watermark|signature|artist_name|dated|web_address|twitter_username|pixiv_id|patreon|copyright_name|character_name|logo$"),
    ("画面", "画质·元数据", r"_challenge$|_username$|_connection$|crossover|^cameo$|^borrowed_|^copyright_notice|^company_name|^page_number|^timestamp|^cover_image|_inset$|^character_profile|^redesign|^official_alternate|^alternate_(color|form|universe|muscle_size)|^scene_reference|^artist_self-insert|^before_and_after|^comparison$|^height_chart|^if_they_mated|^when_you_see_it|^real_life_insert|^through_medium|^too_many$|^odd_one_out|^fewer_digits|^extra_digits|^bad_anatomy"),
    ("人物", "种族·非人", r"_fur$|^fluffy$|^personification|^humanization|^furrification|^monsterification|^objectification|^alien$|^miqo'te|^erune|^draph|^au_ra|^hyur|^elezen|^viera|^lalafell|^harvin|^zora|^gerudo|^sheikah|^yordle|^octoling|^inkling|^taur$|^gills|^hooves|^talons|^snout|^beak$|^pawpads|^tusks|^head_fins|^prosthesis|^joints$|^mechanization|^non-humanoid_robot|^humanoid_robot|^super_robot|^shikigami|^kaiju|^eldritch|^skeleton$|^possessed|^object_head|^headless|^multiple_heads|^extra_faces|^arthropod_limbs|^suction_cups|_scales$|^dinosaur|^digimon_\(creature\)|^clothed_pokemon|^shiny_pokemon|^mega_pokemon|^starter_pokemon|^evolutionary_line|^pokemon_on|^creature_and_personification|^stand_\(jojo\)|^super_saiyan|^psychic$|^telekinesis|^electrokinesis|^levitation"),
    ("服饰", "衣着状态", r"^strapless|^highleg|^lowleg|^skindentation|^impossible_clothes|^undersized_clothes|^baggy_clothes|^shared_clothes|^matching_outfits|^torn$|^tearing_clothes|^popped_button|^crotch_seam|^pantylines|^strap_gap|^midriff_peek|^covered_|^through_clothes|^gusset|^exposed_pocket|^expressive_clothes|^living_clothes|^patchwork_clothes|^multicolored_clothes|^gradient_clothes|^tail_through_clothes|^meme_attire|^two-sided_fabric|^fine_fabric_emphasis|^opened_by_self|^side-tie_peek|^dirty$|^messy$|^stain$|^broken$"),
    ("服饰", "制服·职业装", r"serafuku|^tactical_clothes|^kappougi"),
    ("服饰", "传统服饰", r"^kariginu|^hagoromo|^dudou|_sarong$|^sarong|^ancient_egyptian|^native_american|^tribal"),
    ("服饰", "内衣", r"^sleepwear|^loungewear|^onesie|^trefoil|^panty_straps|^o-ring_bottom|_bandeau$"),
    ("服饰", "上衣", r"_tunic$|^tunic|^bodice|_shrug$|_tabard$|^racerback"),
    ("服饰", "裤子", r"overalls|romper|^cutoffs"),
    ("服饰", "外套·披风", r"robe$|^robe_|^hooded_robe"),
    ("服饰", "首饰·饰品", r"_sash$|^sash|armband|^insignia|^crest$|^plume$|^prayer_beads|^chest_jewel|_pin$|^heart_pendant|^skull_ornament|^star_ornament|^multiple_rings|^gold_chain|^multiple_belts|^chest_strap|^shoulder_strap|^shoulder_boards|^shoulder_spikes|^spiked_armlet|^wrist_guards|^wrist_wrap|^patch$|^drawstring|_button$|^notched_lapels|^snap-fit_buckle|^full-length_zipper|^crotch_zipper|^heart_o-ring|^keyhole$|^safety_pin|^v-fin|^dynamax_band|^vision_\(genshin_impact\)|^kinchaku|^satchel"),
    ("服饰", "泳装·紧身衣", r"innertube|^lifebuoy|^male_swimwear|^snorkel|^spandex|^wading_pool|^one-piece_tan"),
    ("服饰", "鞋子", r"^skates$|^inline_skates|^shoe_soles|^shoe_dangle"),
    ("人物", "面部", r"^veins$|sideburns|beard$|mustache|^snot$|^nostrils|^uvula|_facial_mark$|^facial_mark|^bite_mark|^hickey|^scratches|^cuts$|^injury|^slap_mark|^bruise|^stitches|^head_bump|^long_earlobes|^neck$"),
    ("人物", "身材", r"^height_difference|^size_difference|^mini_person|^height$|^flexible$|^strongman_waist|^sidepec|^covered_abs|^hairy$|^manly$|^spine$|^weight_conscious"),
    ("人物", "人数·性别", r"^faceless_|^ambiguous_gender|^asian$|^friends$|^harem$|^angel_and_devil"),
    ("人物", "身份·职业", r"^detective|^jester|^ballerina|^utaite|^pervert|^female_pervert|^glutton|^jimiko|^team_rocket|^zeon|^sangvis_ferri|^holomyth|^kessoku_band|^ho-kago_tea_time"),
    ("人物", "眼睛", r"sclera"),
    ("人物", "手·手臂", r"fingernails$|^left-handed"),
    ("表情动作", "表情", r"^tearing_up|^teardrop$|sweatdrop|^very_sweaty|^blank_stare|^dark_persona|^come_hither|^unconscious|^sick$|^breath$"),
    ("表情动作", "基础姿势", r"^on_(floor|couch|ground|bench|lap|shoulder|head|grass|rock|stool|railing|person|bed|chair|table|desk|motorcycle)$|^against_|^afloat|^sleeping|^waking_up|^fallen_down|^tripping|^stuck$|^under_covers|^under_kotatsu|^in_bucket|^head_on_pillow|^elbow_rest|^heel_up|^behind_another|^side-by-side"),
    ("表情动作", "其他动作", r"^selfie|^taking_picture|^exercising|^fleeing|^attack$|^incoming_attack|^defeat|^henshin|^confession|^kabedon|^glomp|^high_kick|^fanning_self|^laundry|^reverse_grip|^elbow_carry|^lifting_person|^weightlifting|^livestream|^pouring|^planted$|^unsheathed|^destruction|^failure|^death$|^stab$|^war$|^shared_bathing|^same-sex_bathing|^shared_umbrella|^incoming_gift|^role_reversal|^fusion$|^gameplay_mechanics"),
    ("画面", "特效", r"^glint|^sunburst$|^dark_aura|^paint_splatter|^foam$|^visible_air|^heartbeat|^air_bubble|^crack$|^jaggy_lines|^white_outline|_outline$|^liquid$|^smell$"),
    ("画面", "艺术风格", r"^deformed$|^pale_color|^post-apocalypse|^tokusatsu|^simple_bird"),
    ("画面", "媒介·格式", r"^round_image|^segmented_comic|^square_4koma|^painting_\(object\)|^user_interface|^cursor$|^lyrics|^chemical_structure|^dotted_line|^staff_\(music\)|^roman_numeral|^circled_9|^countdown"),
    ("环境", "季节·节日", r"^year_of_the_"),
    ("环境", "天气·时间", r"^hot$"),
    ("环境", "植物·花", r"_rose$|_lily$|^holly|^wheat|^bud$|^foliage|^overgrown|^log$|_petals$|^leaf_on_head"),
    ("物品", "动物", r"_butterfly$|^tropical_fish|^white_snake|^flock$|^calico|_feathers$|^white_feathers"),
    ("物品", "运动·游戏", r"_\(chess\)$|^dumbbell|^vaulting_horse|^d-pad$|^gamepad|^pom_pom_\(cheerleading\)|^hagoita|^spell_card|^yin_yang_orb"),
    ("物品", "电子设备", r"^machinery|^head-mounted_display|^camcorder|^washing_machine|^electric_fan|^air_conditioner|^electrical_outlet|^electric_plug|^thrusters"),
    ("物品", "其他物品", r"_umbrella$|^oil-paper_umbrella|^closed_umbrella|^skull$|^bone$|^coffin|^tombstone|^corpse|^severed_head|^disembodied_head|^whistle|^sack$|^stick$|^pole$|^shell$|^seashell|^rubber_duck|^tissue|^used_tissue|^sponge|^puppet|^origami|^pinwheel|^chalice|^scepter|^ritual_baton|^sticky_note|^bookmark|^notepad|^marker$|^chalk$|^quill|^tape_measure|^weighing_scale|^thermometer|^spray_can|^cooler$|^kiseru|^mimikaki|^crime_prevention_buzzer|^caution_tape|^teruterubouzu|^fumo_\(doll\)|^haniwa|^sand_sculpture|^party_popper|^heart_balloon|^heart-shaped_pillow|^inflatable_toy|^love_letter|^gold_coin|^holed_coin|^gold$|^explosive|^mechanical_pencil|^pendulum|^winding_key|^round-bottom_flask|^dowsing_rod|^kaleidostick|^mini-hakkero|^bishamonten's_pagoda|^sorcerer's_sutra_scroll|^rod_of_remorse|^magical_musket|^hamaya|^omikuji|^shide$|^kouhaku_nawa|^stone_lantern|^gap_\(touhou\)|^poke_ball|^triforce|^three-dimensional_maneuver_gear|^tokkuri|^choko_\(cup\)|^rice_bowl|^mixing_bowl|^skewer|^cup_ramen|^sanshoku_dango|^paddle|^kine$|^wooden_bucket|^pennant|^union_jack|^puppet_strings|^broken_chain|^noose|^sunscreen|^pointer$|^rolling_suitcase|^crane_\(machine\)|^traffic_cone|^earth_\(ornament\)|^doily|^tablecloth|^drugs"),
    ("场景", "家具·门窗", r"^chalkboard|_fence$|^stone_floor|^stone_stairs|^pavement|^reflective_floor|^stained_glass|^round_window|^lattice|^chimney|^throne|^hammock|^chest_of_drawers|^zabuton|^park_bench|^pool_ladder|^faucet|^barbed_wire"),
    ("场景", "户外·城市", r"^rubble"),
    ("服饰", "裤子", r"jumpsuit"),
    ("服饰", "帽子·头盔", r"bandana$|^wataboushi|^wide_brim|^pom_pom_beanie"),
    ("服饰", "手套", r"gauntlets$|^igote"),
    ("服饰", "首饰·饰品", r"(?<!hair)_ornament$|_buckle$|^laurels|^ankleband|^legband|^character_charm|^keyring|^symphogear_pendant|^han'eri|^motoyui|^toggles|^pankou|^celtic_knot|^front_zipper|^crossed_belts|^black_straps|^kerchief|^bib$|^race_bib|^shoulder_patch|^shoulder_plates|^shoulder_guard|^chest_guard|^gaiters|^undersuit|^singlet|^smock|^haramaki|^kataginu|^chihaya_\(clothing\)|^qixiong_ruqun|^white_hanfu|^gambeson|^c-string|^kittysuit|^serasuku|^glass_slipper|^bike_jersey|^workout_clothes|^high-visibility_clothing|^low-cut|^cowl_neck|^empire_waist|^front_slit|^shihakusho|^bralines|^unfastened|^stained_clothes|^folded_clothes|^painted_clothes|^paint_on_clothes|^dissolving_clothes|^exploding_clothes|^liquid_clothes|^double_strap_slip|^strap_break|^sleeve_rolled_up|^trying_on_clothes"),
    ("场景", "家具·门窗", r"_floor$|_ceiling$|_roof$|^brick|^cobblestone|^concrete|^grate$|^tactile_paving|^on_stairs|^entrance|^noren|^awning|^folding_screen|^getabako|^nightstand|^cupboard|^chaise_longue|^booth_seating|^bath_stool|^squat_toilet|^urinal|^claw_foot_bathtub|^full-length_mirror|^broken_mirror|^broken_window|^fluorescent_lamp|^candelabra|^hedge|^guard_rail|^boom_barrier|^traffic_mirror|^signpost|^flagpole|^clothesline|^swing_set|^slide$|^escalator|^red_carpet|^mat$|^yoga_mat|^air_mattress|^body_pillow|_pillow$|^shared_blanket"),
    ("物品", "其他物品", r"^inflatable_|_balloon$|^menu_board|^wanted_poster|^price_tag|^cash_register|^whiteboard|^board_eraser|^folder|^binder|^paperclip|^papers$|^note$|^package|^carton|^container$|^canister|^canteen|^pitcher_\(container\)|^tankard|^basin|^beaker|^erlenmeyer_flask|^large_syringe|^scalpel|^iv_stand|^intravenous_drip|^crutch|^cast$|^cotton_swab|^razor|^stopwatch|^analog_clock|^diploma|^wax_seal|^hanging_scroll|^incense|^cork|^magnet|^rubber_band|^duct_tape|^sewing_needle|^spool|^fishing_line|^fishing_hook|^cleaning_rag|^feather_duster|^mousetrap|^weights$|^barbell|^paint|^paint_can|^paint_tube|^spray_paint|^art_brush|^nib_pen|^boxcutter|^chisel|^trowel|^circular_saw|^pitchfork|^wheelbarrow|^hishaku|^tuanshan|^hauchiwa|^folded_fan|^kayari_buta|^oonusa|^shakujou|^miracle_mallet|^ruyi_jingu_bang|^fuuin_no_tsue|^hoshi_no_tsue|^grave$|^model_kit|^gunpla|^mannequin|^merchandise|^pile_of_books|^armillary_sphere|^map_\(object\)|^polaroid_photo|^film_strip|^cd_case|^boombox|^audio_jack|^charging_device|^night_vision_device|^oxygen_tank|^parachute|^relay_baton|^starting_block|^kickboard|^lane_line|^flippers|^target$|^lit_fuse|^detonator|^radar|^stick_poster|^penlight|^rina-chan_board|^pokedex|^poketch|^z-ring|^mega_stone|^ring-con|^materia|^saint_quartz|^craft_essence|^holy_grail|^millennium_puzzle|^koban|^yen$|^conch|^clam_shell|^seed$|^acorn|^pinecone|^bonsai|^twig$|^sprout|^plant_roots|^tendril|^hay$|^wool$|^cloth$|^brain$|^organs$|^flesh$"),
    ("表情动作", "其他动作", r"^uppercut|^suplex|^headlock|^choke_hold|^submission_hold|^scissorhold|^kung_fu|^push-ups|^contortion|^picking_up|^pushing_away|^shaking_head|^relaxing|^stargazing|^listening_to_music|^arguing|^massage|^casting_spell|^powering_up|^blowing_smoke|^spit_take|^dogeza|^clinging|^hiding_behind|^washing_another|^human_stacking|^swinging|^at_computer|^biting_clothes|^cracking_knuckles|^mudra|^crossed_wrists|^cross-body_stretch|^assisted_stretching|^modeling|^interview|^delivery|^graduation|^hatsumoude|^marriage_proposal|^prank|^teamwork|^rivalry|^confrontation|^faceoff|^surrounded|^captured|^kidnapped|^trapped|^buried|^immobilization|^entangled|^pinned|^head_pinned_down|^incoming_|^taking_shelter|^remembering|^flashback|^time_stop|^suikawari|^kyuudou|^yukadon|^after_bathing|^after_battle|^in_(bowl|locker|palm|shopping_cart)|^head_on_head|^person_on_head|^creature_on_head|^skull_on_head|^multiple_riders|^peril|^accident|^murder|^suicide|^violence|^poison|^vomit|^fever|^weight_gain|^full_stomach|^disguise|^pose_imitation|^body_switch|^personality_switch|^hairstyle_switch|^decapitation|^windup|^shaft_look|^recursion|^recurring_image"),
    ("表情动作", "表情", r"^curious|^furious|^clueless|^lovestruck|^tantrum|^affectionate|^gesugao|^charisma_break|^head_steam|^spasm|^loving_aura|^uu~|^gao$|^sunken_cheeks"),
    ("人物", "身份·职业", r"^otaku|^fujoshi|^himejoshi|^chuunibyou|^sukeban|^banchou|^onmyouji|^magician|^clown|^cowboy$|^phantom_thief|^tour_guide|^buddhist_nun|^oiran|^army$|^audience|^mojo$|^familiar$|^fallen_angel|^saiyan|^arrancar|^netnavi|^tiefling|^draenei|^lizardman|^female_(goblin|orc)|^half-harpy|^scylla|^bakeneko|^symbiote|^blob$|^zentradi|^tamaranean|^garlean|^elvaan|^ainu$|^aztec$"),
    ("人物", "身体其他部位", r"^large_pectorals|^between_pectorals|^underpec|^armpit_crease|^armpit_peek|^spread_armpit|^crotch$|^body_markings|^markings$|^birthmark|^multiple_moles|^multiple_scars|^scars_all_over|^multiple_piercings|^crossed_bandaids|^gauze_on_cheek|^marking_on_cheek|^drawn_whiskers|^outie_navel|^adam's_apple|^cleft_chin|^mutton_chops|^sparse_stubble|^braces$|^very_hairy|^chest_tuft|^exposed_muscle|^v-taper|^strong$|^heavy$|^mane$|^dorsal_fin|^carapace|^spines$|^stinger|^blowhole|^stitched_|^mechanical_spine|^screw_in_head|^hole_in_chest|^deep_wound|^scrape$|^cuts$|^rayman_limbs|^missing_limb|^object_through_head|^head_only|^between_thighs|^heart_on_chest|^tail_wrap|^tail_raised|^enpera|^blunt_tresses|^red_streaks|^measurements|^alternate_(height|size|pectoral_size|species)"),
    ("画面", "特效", r"^sparkling_aura|^glass_shards|^cracked_|^static$|^gleam|^swirl|^spiral$|^pixel_heart|^winged_heart|^heart_of_string|^star_trail|^dew_drop|^condensation|^rust$|^dirt$|^mud$|^footprints|^translucent|^invisible|^pixelated|^non-circular_lens_flare|^grid$|^scribble|^art_shift|^juxtaposition|^contrast$|^black_vs_white|^front-to-back"),
    ("画面", "文字·符号", r"speech_bubble|^chat_log|^error_message|^hashtag|^episode_number|^initial$|^to_be_continued|^keep_out|^caution|^menacing_\(jojo\)|^source_quote|^cut-here_line|^binary$|^math$|^pleading_face_emoji|^like_and_retweet|^mtu_virus|^neta$|^meta$|^poi$|^nico_nico_nii|^moe_moe_kyun|^so_moe|^you_work_you_lose|^too_literal|^you're_doing_it_wrong|^sugoi_dekai|^tag$|^\\\|\|/$"),
    ("环境", "天空", r"^meteor|^comet|^eclipse|^black_hole|^red_sun|^saturn_\(planet\)|^on_crescent"),
    ("环境", "季节·节日", r"^senkou_hanabi|^good_ass_day|^ehoumaki|^announcement_celebration"),
    ("环境", "植物·花", r"_tulip$|^vegetation|^tropical$|^fluff$"),
    ("物品", "交通工具", r"^dirigible|^biplane|^starfighter|^variable_fighter|^walker_\(robot\)|^evangelion_\(mecha\)|^handlebar|^bridle|^reins$|^sail$|^mast$|^traffic$|^hot_air_balloon|^wind_turbine|^overhead_line|^spire$|^truss$"),
    ("物品", "武器", r"^minigun|^railgun|^artillery|^harpoon|^throwing_needles|^boomerang|^paralyzer|^hook$|^smoking_barrel|^shoulder_cannon|^adapted_turret|^torpedo_tubes|^funnels_\(gundam\)|^gunpod|^particle_cannon|^z_saber|^metal_baseball_bat|^hylian_shield"),
    ("物品", "食物·饮料", r"^red_wine|^hot_chocolate|^mint_chocolate|^hotpot|^ikayaki|^mitarashi_dango|^double_scoop|^strong_zero|^guarana|^in_bowl"),
    ("物品", "动物", r"^chocobo|^white_dog|^multiple_cats|^red_panda|^great_pyrenees|^sacabambaspis|^pikmin|^chao_\(sonic\)|^bangboo|^critter_pick|^mini_dragon|^coral_reef"),
    ("镜头", "景别", r"_out_of_frame$|^cropped_"),
    ("镜头", "焦点", r"_focus$"),
    ("人物", "身体其他部位", r"^shoulder_blades$|^navel$|^stomach$|^belly$|^midriff_peek$"),
    # 拿着东西
    ("表情动作", "拿着东西", r"^holding(_|$)|_in_hand$|^carrying_(?!over)|_in_mouth$"),
    # 人物
    ("人物", "人数·性别", r"^\d+(girls?|boys?|others?)$|^multiple_(girls|boys|others)$|^solo(_focus)?$|^no_humans$|^(male|female|other)_focus$|^everyone$|^crowd$|^people$|^genderswap|^trap$|^otoko_no_ko$|^androgynous$|^tomboy$"),
    ("人物", "年龄", r"^(mature|old|elderly|young|adult|child|toddler|teen|teenage|baby|kid)(_(female|male|man|woman|girl|boy))?$|^aged_|_age$|^age_|^milf$|^dilf$"),
    ("人物", "身材", r"^(muscular|plump|fat|chubby|curvy|skinny|slim|slender|thin|tall|petite|tiny|giant|giantess|minigirl|miniboy|abs|toned|wide_hips|thick_thighs|narrow_waist|pregnant|underbust|hourglass|bodybuilder|biceps|pectorals?|thigh_gap|chibi|huge_ass|large_ass)(_|$)|_figure$|^short_stature$"),
    ("人物", "皮肤", r"_skin$|^skin_|^(dark|pale|tan|tanned|shiny|oily)_?skin|^tanlines?$|^tan$|^dark-skinned|^albino$|freckles|^body_fur$"),
    ("服饰", "发饰", r"hair_(ornament|ribbon|bow|flower|clip|band|pin|tie|bell|stick|bobbles|scrunchie|ring|tubes?|beads|rings|cuffs|bun_cover)|hairclip|hairband|hairpin|scrunchie|kanzashi|^headband$|_hairband$|_headband$|hairpods|^bun_cover$"),
    ("人物", "发色", r"^(%s)_hair$|_hair_color|^two-tone_hair$|^multicolored_hair|^gradient_hair$|^streaked_hair$|^colored_tips$|^colored_inner_hair$|^roots_\(hair\)$|^split-color_hair$|^dyed_" % COLORS),
    ("人物", "发型", r"hair$|_hair_|^hair_|bangs|braid|ponytail|twintails?|sidelocks?|ahoge|bun($|_)|buns$|drill|hime_cut|bob_cut|pixie_cut|^updo|afro|mohawk|undercut|^bald|cowlick|forehead|parted|crew_cut|buzz_cut|_cut$|^one_side_up|^two_side_up|odango|antenna_hair|ringlets|curls?$|_bangs$|^hair$"),
    ("人物", "眼睛", r"_eyes?$|^eyes?_|eyeball|^heterochromia$|^one_eye_|^closed_eyes|^half-closed|^narrowed_eyes|^empty_eyes|^glowing_eye|^tsurime|^tareme|^jitome|^sanpaku|^eye_|_eye_|^@_@$"),
    ("人物", "瞳孔", r"pupils?$|_pupils_|^slit_|^symbol-shaped|^star-shaped_pupils|^heart-shaped_pupils|irises$|_iris$"),
    ("人物", "眉毛·睫毛", r"eyebrow|eyelash|^thick_eyebrows|^unibrow|^hikimayu"),
    ("人物", "嘴巴·牙齿·舌头", r"tongue|teeth|tooth|fang|^lips?$|_lips$|^lips_|mouth|^:[a-z0-9<>]$|^saliva|drooling|^drool|^sharp_teeth|^chestnut_mouth|^parted_lips|^pout|^lip_"),
    ("人物", "耳朵", r"_ears$|^ears?_|^pointy_ears|^ear_|_ear$|^long_pointy_ears|^kemonomimi|^animal_ears"),
    ("服饰", "眼镜·面具", r"eyewear|glasses|goggles|monocle|eyepatch|_mask$|^mask(_|$)|^masked$|blindfold|visor|^veil$|_veil$|^face_veil|^mouth_veil|^respirator"),
    ("人物", "妆容·纹身", r"makeup|lipstick|eyeshadow|eyeliner|mascara|nail_polish|^nail_|_nails$|^nails$|tattoo|^facial_mark|_mark_on_|^forehead_mark|^whisker_markings|^scar(_|$)|_scar$|^mole(_|$)|^beauty_mark|^blush_stickers|^bindi|body_paint|^facepaint|^lip_gloss|_lips_|^cosmetics"),
    ("人物", "胸部", r"breasts?$|^breast_|_breast_|^flat_chest$|^cleavage$|^sideboob$|^underboob$|^backboob$|^chest$|^bust"),
    ("人物", "臀部", r"^ass$|_ass$|^ass_|^butt$|^butt_|^hips$|_hips$|^thick_thighs$|^thighs$|^hip_|^dimples_of_venus"),
    ("人物", "翅膀·尾巴·角", r"(^|_)wings?$|_wings?_|(^|_)tails?$|_tail_|(^|_)horns?$|_horns?_|^halo$|_halo$|^antennae$|^antlers$|^head_wings|^feathers$|^tentacle_hair|^fins?$|^scales$|^dragon_girl$"),
    ("人物", "种族·非人", r"(?<!magical)_girl$|_boy$|_musume$|^(%s)_(girl|boy)|^monster_(girl|boy)|^elf$|^dark_elf$|^vampire|^demon|^angel$|^fairy$|^mermaid|^centaur|^lamia|^harpy|^slime_|^android$|^robot$|^cyborg$|^ghost$|^undead|^zombie|^succubus|^oni$|^yokai|^youkai|^kemono|^furry|^anthro|^doll_joints|^robot_joints|^mechanical_parts|^jiangshi|^dullahan|^arachne|^werewolf|^kitsune$|^nekomata$|^kappa$|^tengu$|^dryad|^satyr|^minotaur|^goblin|^orc$|^elf_" % ANIMALS),
    ("人物", "身份·职业", r"^(maid|nurse|police|policewoman|policeman|miko|nun|priest|priestess|idol|teacher|student|soldier|knight|witch|wizard|ninja|kunoichi|samurai|pirate|princess|prince|queen|king|butler|chef|waitress|waiter|bartender|office_lady|secretary|doctor|scientist|astronaut|pilot|cheerleader|bride|groom|magical_girl|ojou-sama|gyaru|kogal|delinquent|yankee|hero|villain|warrior|mage|archer|sniper|gunner|dancer|singer|musician|athlete|streamer|vtuber|virtual_youtuber|cosplay|sister|siblings|brothers|sisters|twins|couple|husband|wife|girlfriend|boyfriend|yuri|lovers|family|mother|father)$|_cosplay$|^(mother|father|brother|sister)_and_"),
    ("人物", "手·手臂", r"^hands?$|^fingers?$|^fingernails|^palms?$|^arms?$|^armpits?$|^biceps|^wrists?$|^knuckles|^thumbs?($|_)|^index_finger|^fist$|^claws$|^arm_hair"),
    ("人物", "腿·脚", r"^legs?$|^thighs?$|^feet$|^foot$|^soles$|^toes$|^toenails|^knees?$|^calves$|^ankles?$|^barefoot$|^bare_legs$|^long_legs$|^kneepits$|^toe_(scrunch|curl|spread)"),
    ("人物", "面部", r"^face$|_face$|^face_|^cheek|^chin$|^chin_|^nose$|_nose$|^nose_|^forehead$|^jaw|^beard|^mustache|^stubble|^goatee|^facial_hair|^blush$|^light_blush|^full-face_blush|^nosebleed|^sweat$|^sweating|^tears$|^streaming_tears|^profile$|^portrait$"),
    # 服饰
    ("服饰", "鞋子", r"footwear|shoes?$|_shoes?_|boots?$|_boots_|sneakers|sandals?$|high_heels|heels$|loafers|mary_janes|slippers|geta$|zouri|okobo|uwabaki|platform_|clogs|flip-flops|pumps$"),
    ("服饰", "袜子·腿饰", r"legwear|thighhighs|pantyhose|socks?$|_socks_|kneehighs|leggings|leg_warmers|stockings|thigh_strap|garter|^thighband|loose_socks|tabi|fishnets$|leg_ribbon|anklet|ankle_"),
    ("服饰", "手套", r"gloves?$|_gloves_|mittens|^gauntlets?|^bracer|wristband|wrist_cuffs|^vambraces"),
    ("服饰", "袖子", r"sleeves?$|_sleeves_|^sleeveless$|^sleeves_|^detached_sleeves|^puffy_|^juliet_sleeves|cuffs$"),
    ("服饰", "内衣", r"(^|_)bra$|^bra_|panties|underwear|lingerie|thong|fundoshi|briefs|boxers|bloomers|garter_belt|negligee|babydoll|camisole|corset|bustier|chemise|nightgown|pajamas|^g-string|^boyshorts|^lace_bra|_bra_|undershirt|^sarashi"),
    ("服饰", "泳装·紧身衣", r"swimsuit|bikini|leotard|bodysuit|playboy_bunny|bunnysuit|plugsuit|wetsuit|rash_guard|^monokini|competition_swimsuit|^swim_|bikesuit|racing_suit|catsuit|unitard|bodystocking|latex_suit|skin_tight"),
    ("服饰", "连衣裙", r"(?<!head)dress$|_dress_|^dress_|^gown$|_gown$|sundress|qipao|china_dress|cheongsam|^frock"),
    ("服饰", "裙子", r"skirt|^kilt$|^hakama$|_hakama$|^tutu$"),
    ("服饰", "裤子", r"shorts|pants|jeans|trousers|^buruma|_buruma$|^hotpants|^capri|^overalls|^shorts$|^dolphin_shorts|^bike_shorts|^sweatpants|^chaps$"),
    ("服饰", "外套·披风", r"jacket|coat$|_coat_|^coat|cardigan|^cape$|_cape$|^cape_|capelet|cloak|^vest$|_vest$|^vest_|hoodie|^hood$|_hood$|^hood_|parka|blazer|poncho|shawl|^haori|^shrug|^bolero|^windbreaker|^raincoat|^mantle"),
    ("服饰", "上衣", r"shirt|blouse|sweater|tank_top|crop_top|tube_top|^top$|_top$|^turtleneck|^halterneck|^tunic|^jersey|^t-shirt|^polo|^tee$|^sailor_collar|^off-shoulder|^bandeau|^chest_sarashi|^sweatshirt|^pullover"),
    ("服饰", "领口·领带·颈饰", r"necktie|^tie$|_tie$|bowtie|choker|collar(ed)?($|_)|scarf|necklace|neckerchief|ascot|neck_ribbon|^neckwear|_neckwear|^stole$|^boa$|feather_boa|^pendant|^lanyard|^bolo_tie|^jabot|^neck_"),
    ("服饰", "帽子·头盔", r"hat$|_hat_|^hat_|^hat$|^cap$|_cap$|beret|helmet|^hood_up|^crown$|_crown$|tiara|diadem|circlet|^bonnet|^beanie|^headdress|^headgear|^headpiece|^headwear|_headwear|^kepi|^fedora|^tricorne|^bicorne|^top_hat|^witch_hat|^mob_cap|^nurse_cap|^garrison_cap|^peaked_cap|^headphones_around|^head_scarf|^bandana$|^hachimaki|^tokin|^turban|^veil_|^maid_headdress"),
    ("服饰", "首饰·饰品", r"earrings?|bracelet|^rings?$|_ring$|jewelry|brooch|gem$|gemstone|^jewel|^pendant|^amulet|^talisman|^bangle|^armlet|^armband|^piercing|_piercing$|^belly_chain|^body_chain|^ribbon$|_ribbon$|^bow$|_bow$|^badge|_badge$|^pin$|^button_badge|^medal|^rosary|^cross_necklace|^bell$|_bell$|^belt$|_belt$|^belt_|^sash|^obi$|^obiage|^obijime|^pouch|^bag_charm|^keychain|^strap$|^suspenders|^harness|^tassel|^charm_|^watch$|^wristwatch|^bead"),
    ("服饰", "盔甲", r"armor|^pauldrons|^breastplate|^greaves|^shoulder_armor|^faulds|^gorget|^chainmail|^cuirass|^power_suit|^power_armor|^exoskeleton|^shield$"),
    ("服饰", "传统服饰", r"kimono|yukata|furisode|haori|happi|^hanfu|^chinese_clothes|^china_|^ao_dai|^hanbok|^sari$|^dirndl|^miko_|^japanese_clothes|^fundoshi|^jinbei|^samue|^tangzhuang|^changpao|^ruqun|^beizi|^shenyi|^tabard|^toga|^chiton|^arabian_clothes|^traditional_clothes|^traditional_"),
    ("服饰", "制服·职业装", r"uniform|^serafuku|^school_|^maid_|^nurse_|^police_|^military$|^military_uniform|^waitress|^apron|_apron$|^suit$|_suit$|^business_suit|^tuxedo|^labcoat|^lab_coat|^gakuran|^sailor_|^gym_|^costume|_costume$|^outfit|_outfit$|^santa_|^halloween_costume|^pilot_suit|^track_suit|^tracksuit|^nun_|^habit$|^cassock|^vestment|^gi$|^dougi|^idol_clothes|^cheerleader_|^race_queen|^bunny_|^cosplay"),
    ("服饰", "风格·时尚", r"fashion|^lolita|_lolita$|^casual$|^formal$|^streetwear|^punk|^goth|^gothic|^steampunk|^cyberpunk_|^techwear|^gyaru|^kogal|^ganguro|^decora|^jirai_kei|^yami_kawaii|^y2k|^preppy|^bohemian|^sportswear|^biker_clothes|^alternate_costume|^adapted_costume|^casual_"),
    ("服饰", "花纹·材质", r"_print$|^print_|striped|stripes$|plaid|polka_dot|checkered|argyle|camouflage|houndstooth|gingham|tartan|paisley|floral|frill|lace|see-through|transparent(?!_background)|latex|leather|^fur(-|_|$)|denim|silk|satin|velvet|knit|ribbed|mesh|fishnet|sequins|glitter|metallic|patterned|_pattern$|^pattern|_trim$|-trimmed|^layered|^pleated|^ruffle|^embroider|^brocade|^lace-up|cross-laced|^zipper|^buttons|^double-breasted|^cutout|_cutout$|^clothing_cutout|^center_opening|^shiny_clothes"),
    ("服饰", "衣着状态", r"^wet_|_wet$|^torn_|^open_|^unbuttoned|^untied|^undone|^loose_|^tight_|^oversized_|^unworn_|^clothes_|_aside$|_pull$|_lift$|^adjusting_|^off_shoulder|^strap_slip|^bare_|^no_|^single_|^mismatched_|^asymmetrical_clothes|^clothes$|^clothing|^naked_|^shirt_tucked|^untucked|^dressing|^undressing|^changing_clothes|^taut_|^rolled_up|^sleeves_rolled|^dirty_clothes|^bloody_clothes|^burnt_clothes|^damaged|^wardrobe"),
    # 表情动作
    ("表情动作", "视线", r"^looking_|^eye_contact$|^staring|^gaze|^glaring|^averting_eyes|^side_glance|^head_tilt$|^facing_|^peeking"),
    ("表情动作", "表情", r"smile|smirk|grin|laugh|blush|crying|tears|^cry$|sad$|angry|anger|annoyed|embarrass|surprised|shocked|scared|nervous|confused|frown|pout|serious|expressionless|(^|_)happy$|^smug|^disgust|^despair|^sleepy|^tired|^bored|^shy|^excited|^scowl|^wince|^panicking|^worried|^jealous|^lonely|^determined|^naughty|^seductive|^evil|^crazy|^yandere|^tsundere|^kuudere|^:[^\s]*$|^;[^\s]*$|^[^a-z0-9]*[<>^@\-_=;:.oOxX3]+[^a-z]*$|^o_o$|^x_x$|^=_=$|^\^_\^$|^>_<$|^d:$|^xd$|^dx$|^uwu$|^owo$|_face$|^expression|^emotion|^facepalm|^sigh|^sweatdrop|^flustered|^gloom|^pale_face|^shaded_face|^turn_pale|^nose_blush|^ear_blush|^spoken_|^\?$|^!$|^!!$|^\.\.\.$"),
    ("表情动作", "手势", r"^v$|^double_v|_v$|^peace_sign|^thumbs?_|^ok_sign|^pointing|^finger_gun|^finger_heart|^heart_hands|_heart_hands|^salute|^waving|^wave$|^beckoning|^shushing|^middle_finger|^\\m/|^\\n/|^fist_|^clenched_hand|^open_hand|^claw_pose|^paw_pose|^rabbit_pose|^fox_shadow_puppet|^crossed_fingers|^pinky_|^index_finger_raised|^akanbe|^bunny_pose|^horns_pose|^steepled_fingers|^own_hands_|^hands_together|^praying|^fingers_together|^gesture|_gesture$|^shaka_sign|^l_|^w_|^money_gesture|^air_quotes|^cupping_hands"),
    ("表情动作", "多人互动", r"(^|_)hug(s|ging)?(_|$)|kiss|^holding_hands|^hand_holding|interlocked_fingers|^carrying|^piggyback|^princess_carry|^shoulder_carry|headpat|^patting|^petting|^lap_pillow|^sitting_on_(lap|person|shoulder)|^cheek-to-cheek|^face-to-face|^forehead-to-forehead|^back-to-back|^nose-to-nose|^eye_contact|^arm_around|^arms_around|^hand_on_another|^hands_on_another|_on_another's|another's_|^cuddling|^spooning|^embrac|^feeding|^teasing|^tickling|^poking|^slapping|^punching|^kicking|^fighting$|^battle$|^duel$|^sparring|^wrestling|^tug_of_war|^high_five|^handshake|^fist_bump|^pinky_swear|^leaning_on_person|^head_on_another|^couple|^date|^multiple_persona|^group_hug|^holding_another"),
    ("表情动作", "拿着东西", r"^holding"),
    ("表情动作", "手臂动作", r"^arms?_|_arms?$|_arms?_|^arm$|^flexing|^reaching|^outstretched|^stretching|^crossed_arms|^v_arms|^airplane_arms|^shrug|^akimbo|^spread_arms|^raised_|^salute"),
    ("表情动作", "手部动作", r"^hands?_(?!fan)|_hands?$|_hand_|^hand$|^finger_|_fingers?$|^fingers_|^covering_|^clenched_|^grabbing|_grab$|^pinching|^tugging|^pulling|^touching|^scratching|^rubbing|^playing_with_own|^twirling|^adjusting|^tying|^untying|^wiping|^cupping|^palms?$|^palm_(?!tree)|^thumb_|^index_finger|^own_hands"),
    ("表情动作", "腿部动作", r"^legs?_|_legs?$|_legs?_|^knees?_|_knees?$|^kneeling|^sitting|^seiza|^wariza|^squatting|^crouching|^crossed_ankles|^indian_style|^lotus_position|^butterfly_sitting|^yokozuwari|^straddling|^kicking|^tiptoes|^on_one_knee|^standing_on_one_leg|^leg_|^foot_|^feet_|_feet$|_foot$|^toes_|^spread_legs|^m_legs|^split$|^splits"),
    ("表情动作", "基础姿势", r"^standing|^lying|^on_back|^on_stomach|^on_side|^all_fours|^leaning|^bent_over|^arched_back|^jumping|^running|^walking|^falling|^floating|^flying|^crawling|^midair|^dynamic_pose|^pose$|_pose$|^posing|^stance|_stance$|^contrapposto|^upside-down|^handstand|^reclining|^slouching|^hunched|^head_rest|^arm_support|^curled_up|^fetal_position|^balancing|^dancing|^twisted_torso|^turning|^spinning|^top-down_bottom-up|^prostration|^bowing|^head_down|^head_back|^head_tilt"),
    # 镜头
    ("镜头", "景别", r"^(upper|lower|full)_body$|^cowboy_shot$|^portrait$|^close-up$|^extreme_close-up|^wide_shot$|^very_wide_shot|^medium_shot|^bust_shot|^head_out_of_frame|_out_of_frame$|^cropped_|^feet_out|^face_out|^eyes_out|^lower_body|^upper_body|^full_body|^half_body|_shot$|^headshot"),
    ("镜头", "角度", r"^from_|_view$|^pov($|_)|^dutch_angle|_angle$|^fisheye|^foreshortening|^perspective$|^vanishing_point|^three_quarter|^profile$|^straight-on$|^facing_viewer|^facing_away|^back$|^rear_view"),
    ("镜头", "焦点", r"_focus$|^focus$|^depth_of_field|^blurry|^bokeh|^soft_focus|^out_of_focus|^chromatic_aberration|^motion_blur|^tilt-shift"),
    ("镜头", "构图", r"^multiple_views|^split_screen|^split_frame|^border|_border$|^frame$|_frame$|^framed|^inset|^comic$|^panels?|^symmetry|^symmetrical|^centered|^rule_of_thirds|^diagonal|^silhouette|^reflection|^mirror_image|^negative_space|^cropped|^letterboxed|^pillarboxed|^vignett|^zoom_layer|^variations|^character_sheet|^reference_sheet|^turnaround|^lineup|^collage|^diptych|^triptych|^afterimage"),
    # 画面
    ("画面", "背景", r"background$|^background_|^scenery|^landscape$|^no_background|^transparent_background|^simple_background"),
    ("画面", "光照", r"light(ing)?$|_light_|^light_|lighting|^sunlight|^moonlight|^backlit|^rim_|^shadow|_shadow$|shade$|^glow|_glow$|glowing|^lens_flare|^light_rays|^sunbeam|^crepuscular|^god_rays|^dappled|^spotlight|^neon|^dark$|^darkness|^chiaroscuro|^bloom$|^caustics|^shine|^shiny$|^sparkle|^twinkle"),
    ("画面", "颜色", r"_theme$|^monochrome|^greyscale|^grayscale|^sepia|^colorful|^pastel|^muted_color|^limited_palette|^spot_color|^partially_colored|^high_contrast|^low_contrast|^inverted_colors|^color_|_colors$|^vivid|^saturat|^desaturat|^black_and_white|^duotone|^flat_color|^gradient$|^rainbow$|^hue"),
    ("画面", "艺术风格", r"_\(style\)$|_style$|^style_|^realistic|^photorealistic|^semi-realistic|^anime_coloring|^anime_screencap|^retro_artstyle|^traditional_media|^watercolor|^oil_painting|^acrylic|^pastel_\(medium\)|^sketch|^lineart|^line_art|^ink|^pencil|^crayon|^marker_\(medium\)|^colored_pencil|^chibi|^super_deformed|^pixel_art|^3d$|^cel_shading|^impressionism|^ukiyo-e|^art_nouveau|^art_deco|^pop_art|^abstract|^surreal|^minimalism|^vaporwave|^synthwave|^cyberpunk$|^steampunk$|^fantasy$|^science_fiction|^sci-fi|^horror|^dark_fantasy|^cartoon|^western_comics|^manga|^painterly|^impasto|^nihonga|^faux_|^parody|_parody$|^fine_art|^toon|^rubber_hose|^flat_|^outline|^thick_lines|^no_lineart|^sketchbook"),
    ("画面", "媒介·格式", r"_\(medium\)$|^4koma|^comic_|^manga_|^doujin|^cover$|_cover$|^cover_page|^magazine(?!_\(weapon\))|^poster|^album|^wallpaper|^official_art|^promotional|^key_visual|^game_cg|^screenshot|_screenshot$|^sprite|^card_|^trading_card|^pinup|^calendar|^scan$|^photo_|^photograph|^cosplay_photo|^tegaki|^oekaki|^animated|^animation|^gif$|^video$|^webm|^storyboard|^concept_art|^design|^character_design|^model_sheet|^dakimakura|^tapestry|^shikishi|^postcard|^nengajou|^sticker|^emoji|^icon$|^avatar"),
    ("画面", "特效", r"^particles?$|_particles$|^sparkles?$|^bubbles?$|^light_particles|^petals$|^confetti|^motion_lines|^speed_lines|^emphasis_lines|^action_lines|^impact|^explosion|^smoke|^aura|^energy|^magic$|^magic_circle|^sparks|^lightning|^electricity|^fire_|^flames?$|^embers|^steam$|^mist$|^fog$|^haze|^glitch|^distortion|^chromatic|^double_exposure|^film_grain|^noise$|^halftone|^dithering|^scanlines|^crt|^vhs|^blood$|^blood_|_blood$|^splatter|^splash|^ripples|^water_drop|^raindrop|^dust|^debris|^shards|^shattered|^broken_glass|^afterimage|^trail|^beam|^laser|^shockwave|^heart_\(symbol\)|^floating_hearts|^spoken_heart|^musical_note$|^notes$"),
    ("画面", "文字·符号", r"text$|_text_|^text_|^speech_bubble|^thought_bubble|^dialogue|^onomatopoeia|^sound_effects|^sfx|^caption|^subtitle|^title$|^letter$|^writing|^handwriting|^calligraphy|^kanji|^hiragana|^katakana|^romaji|^hangul|^alphabet|^number|^numbered|^character_name|^symbol|_symbol$|_\(symbol\)$|^heart$|^star_\(symbol\)|^question_mark|^exclamation|^arrow_\(symbol\)|^emblem|_emblem$|_\(emblem\)$|^logo|_logo$|^flag$|_flag$|^sign$|_sign$|^signboard|^banner|^label|^tag_|^barcode|^qr_code|^pun$|^engrish|^ascii|^kaomoji|^emoticon|^\d+$"),
    # 环境
    ("环境", "季节·节日", r"^spring_\(season\)|^summer$|^autumn$|^fall_\(season\)|^winter$|^season|christmas|halloween|valentine|new_year|easter|birthday|anniversary|tanabata|hinamatsuri|setsubun|^festival|_festival$|^matsuri|^obon|^tsukimi|^thanksgiving|^chinese_new_year|^lunar_new_year|^happy_|^merry_|^santa|^jack-o'-lantern|^kadomatsu|^fireworks"),
    ("环境", "天气·时间", r"^rain$|^rainy|^raining|_rain$|^snow$|snowing|snowflake|^wind$|^windy|^storm$|^thunderstorm|^thunder|^lightning$|^fog|^mist$|^cloudy|^sunny|^weather|^day$|^daytime|^night$|^nighttime|^evening|^morning$|^dawn|^dusk$|^twilight|^sunset|^sunrise|^golden_hour|^blue_hour|^midnight$|^noon|^overcast|^hail|^tornado|^rainbow$|^puddle|^wet$|^heat$|^cold$"),
    ("环境", "天空", r"sky$|_sky_|^sky_|cloud|^sun$|^moon$|_moon$|^moon_|^full_moon|^crescent_moon|^star_\(sky\)|^stars$|^starry|^shooting_star|^constellation|^milky_way|^galaxy|^nebula|^space$|^outer_space|^planet|^earth_\(planet\)|^aurora|^contrail|^horizon|^skyline"),
    ("环境", "水·冰·火", r"^water$|^water_(?!bottle|gun|melon)|_water$|^ocean|^sea$|^river|^lake|^pond|^stream|^waterfall|^waves|^wave$|^splash|^bubbles?$|^underwater|^ice$|^ice_(?!cream)|_ice$|^icicle|^frozen|^fire$|^flame|^burning|^lava|^magma|^smoke$|^steam|^droplet|^water_drop|^wet$|^submerged|^partially_submerged|^swimming|^diving|^bathing|^onsen|^hot_spring"),
    ("环境", "植物·花", r"flowers?$|_flowers?_|^flower_|^petals|^rose($|_)|^lily_|^tulip|^sunflower|^cherry_blossoms|^sakura|^hydrangea|^lotus$|^daisy|^lavender_\(flower\)|^orchid|^poppy|^camellia|^chrysanthemum|^morning_glory|^wisteria|^hibiscus|^dandelion|^clover|^four-leaf|^leaf$|^leaves|_leaf$|^tree$|_tree$|^trees$|^tree_|^grass|^plant$|_plant$|^plants$|^bush|^vines?$|^ivy|^moss|^bamboo|^palm_tree|^cactus|^mushroom|^branch|^forest|^bouquet|^wreath|^garland|^seaweed|^fern|^maple|^ginkgo|^autumn_leaves|^falling_leaves|^falling_petals|^potted_plant|^flower_pot|^flowerbed|^herb"),
    # 场景
    ("场景", "家具·门窗", r"^bed$|_bed$|^bed_|^bedroom$|^chair$|_chair$|^table$|_table$|^desk$|_desk$|^sofa|^couch|^bench$|^stool|^window|^door|^curtains?|^blinds|^shelf|^shelves|^bookshelf|^cabinet|^drawer|^wardrobe$|^closet|^pillow|^cushion|^blanket|^futon|^bedsheet|^sheets$|^mattress|^lamp|^chandelier|^carpet|^rug$|^tatami|^shouji|^fusuma|^kotatsu|^mirror$|^vanity|^dresser|^fireplace|^stairs|^staircase|^railing|^handrail|^balcony|^fence|^gate$|^torii|^furniture|^counter$|^bathtub|^toilet|^sink$|^shower|^locker|^vending_machine|^clock$|^wall_clock|^ceiling|^floor$|^wooden_floor|^tiles|^tile_floor|^wall$|_wall$|^brick_wall|^pillar|^column$|^shoji"),
    ("场景", "室内", r"^indoors|(^|_)room$|_room_|^bedroom|^classroom|^kitchen$|^bathroom|^office|^library|^hallway|^corridor|^living_room|^dining|^restaurant|^cafe|^bar$|^shop$|^store$|^convenience_store|^supermarket|^gym$|^locker_room|^changing_room|^infirmary|^hospital|^church$|^cathedral|^temple$|^shrine$|^dungeon|^prison$|^jail|^cell$|^basement|^attic|^stage$|^theater|^cinema|^arcade|^karaoke|^bath$|^public_bath|^sauna|^onsen_|^train_interior|^car_interior|^airplane_interior|^spacecraft_interior|_interior$|^cockpit|^elevator|^laboratory|^lab$|^workshop|^studio|^warehouse|^factory|^nursery|^dojo|^tea_house|^ballroom|^throne_room|^castle_interior"),
    ("场景", "户外·自然", r"^outdoors|^beach$|^shore|^coast|^seaside|^island|^cave|^canyon|^cliff|^mountain|^hill|^valley|^field|^meadow|^grassland|^prairie|^savanna|^desert$|^dune|^jungle|^rainforest|^swamp|^marsh$|^wasteland|^volcano|^glacier|^tundra|^oasis|^nature|^wilderness|^countryside|^rural|^farm|^rice_paddy|^garden|^park$|^forest|^woods|^path$|^trail|^dirt_road|^rock$|^rocks$|^boulder|^cave_|^waterfall|^riverbank|^lakeside|^sandbar|^sand$|^ruins|^landscape"),
    ("场景", "户外·城市", r"^city|^town|^village|^street|^road|^alley|^sidewalk|^crosswalk|^intersection|^highway|^bridge|^rooftop|^parking|^train_station|^bus_stop|^platform|^railroad|^railway|^train_tracks|^harbor|^port$|^pier|^dock|^plaza|^square$|^market|^shopping$|^shopping_(mall|district|street)|^amusement_park|^ferris_wheel|^carousel|^playground|^schoolyard|^campus|^stadium|^pool$|^poolside|^swimming_pool|^water_park|^cityscape|^skyscraper|^building$|^buildings|^power_lines|^utility_pole|^street_lamp|^lamppost|^traffic_light|^road_sign|^neon_sign|^graffiti|^tokyo|^shibuya|^akihabara|^shinjuku|^urban|^downtown|^suburb|^construction_site|^battlefield|^military_base|^airport|^runway|^port"),
    ("场景", "建筑", r"architecture|^castle|^palace|^tower|_tower$|^temple|^shrine|^pagoda|^church|^cathedral|^mosque|^houses?$|^mansion|^apartment|^school$|^school_building|^hospital|^lighthouse|^windmill|^ruins|^gazebo|^pavilion|^gate|^wall$|^fortress|^dome|^arch$|^archway|^colonnade|^stairs|^balcony|^veranda|^porch|^engawa|^japanese_architecture|^east_asian_architecture|^chinese_architecture|^gothic_architecture|^european_architecture|^western_architecture|^greco-roman_architecture|^industrial|^cyberpunk_city|^fantasy_city"),
    ("场景", "现实地点", r"^japan$|^china$|^korea$|^south_korea$|^america$|^united_states$|^france$|^germany$|^italy$|^russia$|^united_kingdom$|^england$|^spain$|^india$|^brazil|^canada|^australia|^mount_fuji|^eiffel_tower|^statue_of_liberty|^tokyo_|^kyoto|^osaka|^paris|^london|^new_york|^venice|^hong_kong|^taiwan|^thailand|^vietnam|^egypt|^greece|^rome|^roman_empire|^soviet|^nazi"),
    # 物品
    ("物品", "武器", r"weapon|sword|katana|(?<!shoulder)_blades?$|^blades?$|knife|dagger|^gun$|_gun$|^gun_|rifle|pistol|revolver|shotgun|handgun|firearm|^smg$|submachine|machine_gun|^spear|^lance|polearm|halberd|naginata|^axe$|_axe$|^bow_\(weapon\)|crossbow|^arrow_\(projectile\)|^arrow$|^quiver|^shield|^scythe|^staff$|_staff$|^wand$|_wand$|^sheath|^scabbard|^bullet|ammunition|^ammo|^cartridge|^grenade|^bomb|^missile|^rocket|^cannon|^turret|^tank_\(vehicle\)|^tank$|^mace|^hammer$|^warhammer|^flail|^whip$|^nunchaku|^shuriken|^kunai|^tonfa|^trident|^chakram|^claw_\(weapon\)|^scope|^trigger|^holster|^magazine_\(weapon\)|^muzzle|^bayonet|^sniper|^m\d|^ak-|^ar-|^h&k|^sig_|^fn_|^glock|^beretta|^colt|^walther|^desert_eagle|^mp\d|^pp|^type_\d+|^excalibur|^gae_|^kanshou|^zanpakutou|^keyblade|^gunblade|^lightsaber|^energy_sword|^beam_saber|^chainsaw|^baseball_bat|^nail_bat|^brass_knuckles|^molotov|^flamethrower|^rpg|^bazooka|^panzerfaust|^launcher|_launcher$"),
    ("物品", "食物·饮料", r"food|fruit|^apple|^banana|^orange_\(fruit\)|^lemon|^strawberr|^cherry$|^cherries|^grapes|^peach$|^melon|^watermelon|^pineapple|^mango|^kiwi|^blueberr|^raspberr|^cake|_cake$|^cupcake|^pie$|_pie$|^cookie|^biscuit|^cracker|^chocolate|^candy|_candy$|^lollipop|^ice_cream|^popsicle|^parfait|^pudding|^dessert|^sweets|^donut|^doughnut|^macaron|^mochi|^dango|^wagashi|^taiyaki|^dorayaki|^onigiri|^rice$|^sushi|^sashimi|^ramen|^noodles|^udon|^soba|^pasta|^spaghetti$|^pizza|^burger|^hamburger|^sandwich|^hot_dog|^bread|^toast|^croissant|^baguette|^pancake|^waffle|^crepe|^egg$|^eggs$|^fried_egg|^omelet|^omurice|^curry|^soup|^stew|^salad|^vegetable|^carrot|^tomato|^potato|^onion|^cabbage|^corn$|^cucumber|^eggplant|^pumpkin|^radish|^daikon|^meat|^steak|^bacon|^sausage|^ham$|^chicken_\(food\)|^fried_chicken|^fish_\(food\)|^shrimp|^tempura|^takoyaki|^okonomiyaki|^gyoza|^dumpling|^baozi|^bento|^lunchbox|^drink|^beverage|^tea$|_tea$|^teacup|^teapot|^coffee|^cup$|_cup$|^mug$|^glass$|^drinking_glass|^wine|^beer|^sake|^alcohol|^cocktail|^champagne|^whiskey|^juice|^milk$|^soda|^cola|^ramune|^bottle|_bottle$|^can$|^canned|^straw$|^drinking_straw|^bubble_tea|^tapioca|^cream$|^whipped_cream|^honey|^jam$|^butter$|^cheese|^ketchup|^mayonnaise|^sauce|^spoon|^fork$|^chopsticks|^knife_\(food\)|^plate$|^bowl$|^tray$|^lunch|^dinner|^breakfast|^meal|^snack|^chips|^popcorn|^pocky|^nuts?$|^peanut|^almond|^chestnut|^berry|^citrus|^grapefruit|^lime|^coconut|^avocado|^tofu|^natto|^miso|^kimchi|^tamagoyaki|^nikuman|^yakisoba|^yakitori|^kebab|^oden|^sukiyaki|^shabu|^hot_pot|^nabe|^eating|^cooking|^baking|^kitchen_knife|^frying_pan|^pot$|^kettle"),
    ("物品", "动物", r"^(%s)s?$|^(%s)_(on|in|and|with)_|_\(animal\)$|^animals?$|^animal_(?!ear)|(?<!stuffed)_animal$|^pet$|^bug$|^insect|^fish$|^bird$|^birds$|^cat$|^dog$|^horse|^pony|^cattle|^livestock|^creature$|^pokemon_\(creature\)|^shiba_inu|^corgi|^husky|^retriever|^poodle|^dachshund|^pug$|^chihuahua|^parrot|^pigeon$|^dove|^sparrow|^swallow|^seagull|^swan|^flamingo|^peacock|^crane_\(animal\)|^hawk|^falcon|^raven|^stingray|^jellyfish|^starfish|^squid|^lobster|^shrimp_\(animal\)|^snail|^slug|^worm|^caterpillar|^ladybug|^dragonfly|^firefly|^moth$|^ant$|^beetle|^cicada|^grasshopper|^mantis|^scorpion|^centipede|^koi|^goldfish|^tuna|^salmon|^sea_slug|^axolotl|^capybara|^chinchilla|^guinea_pig|^mole_\(animal\)|^platypus|^armadillo|^anteater|^bison|^buffalo|^yak|^gazelle|^antelope|^rhino|^hippo|^gorilla|^chimpanzee|^orangutan|^lemur|^meerkat|^badger|^skunk|^opossum|^porcupine|^beaver|^walrus|^sea_lion|^manatee|^penguins|^pelican|^toucan|^hummingbird|^kingfisher|^woodpecker|^chick$" % (ANIMALS, ANIMALS)),
    ("物品", "交通工具", r"vehicle|^car$|_car$|^car_|^cars$|^truck|^bus$|^van$|^taxi|^motorcycle|^motorbike|^scooter|^bicycle|^bike$|^unicycle|^skateboard|^roller_skates|^rollerblades|^train$|_train$|^train_|^locomotive|^subway|^tram|^monorail|^ship$|_ship$|^boat|_boat$|^yacht|^canoe|^kayak|^raft|^submarine|^airplane|^aircraft|^jet$|^fighter_jet|^helicopter|^airship|^blimp|^spaceship|^spacecraft|^rocket_ship|^ufo|^mecha$|^mecha_|^robot_\(mecha\)|^gundam|^tank_\(vehicle\)|^military_vehicle|^ambulance|^police_car|^fire_truck|^tractor|^forklift|^excavator|^carriage|^cart$|^wagon|^sled|^sleigh|^wheelchair|^stroller|^shopping_cart|^jeep|^suv|^sports_car|^porsche|^ferrari|^lamborghini|^toyota|^honda_|^nissan|^mazda|^bmw|^mercedes|^volkswagen|^ford_|^chevrolet|^vespa|^cub$|^steering_wheel|^license_plate|^tire|^wheel$|^headlight|^dashboard|^seatbelt|^driving|^riding"),
    ("物品", "乐器·音乐", r"guitar|piano|violin|cello|viola|bass_\(instrument\)|^bass_guitar|drum|^instrument|_instrument$|^flute|^recorder|^trumpet|^trombone|^saxophone|^clarinet|^oboe|^harp$|^harmonica|^accordion|^ukulele|^banjo|^mandolin|^shamisen|^koto|^biwa|^erhu|^guzheng|^pipa|^taiko|^tambourine|^triangle_\(instrument\)|^xylophone|^keyboard_\(instrument\)|^synthesizer|^keytar|^microphone|^mic$|^music$|^musical_note|^sheet_music|^music_stand|^conductor|^baton_\(conducting\)|^amplifier|^speaker|^headphones|^earphones|^earbuds|^dj|^turntable|^record$|^vinyl|^cassette|^cd$|^singing|^playing_instrument|^band$|^concert|^live_|^idol_\(performance\)|^plectrum|^pick_\(music\)"),
    ("物品", "电子设备", r"phone|^smartphone|^cellphone|^mobile_phone|^computer|^laptop|^pc$|^desktop|^monitor|^screen$|^tablet|^ipad|^television|^tv$|^crt|^keyboard$|^computer_keyboard|^mouse_\(computer\)|^computer_mouse|^camera|^video_camera|^webcam|^game_console|^game_controller|^controller|^handheld_game|^nintendo|^playstation|^xbox|^gameboy|^game_boy|^switch_\(console\)|^joy-con|^vr_headset|^headset|^earpiece|^radio|^walkie-talkie|^speaker|^remote_control|^calculator|^charger|^cable|^wire$|^usb|^battery|^robot$|^drone|^satellite|^server|^hologram|^holographic|^projector|^printer|^fax|^pager|^gps|^smartwatch|^digital|^electronic|^led|^circuit|^computer_chip|^hard_drive|^sd_card|^floppy|^ipod|^iphone|^walkman|^mp3|^stylus|^drawing_tablet|^pen_tablet"),
    ("物品", "运动·游戏", r"^ball$|_ball$|^ball_|^balls$|^soccer|^football|^baseball|^basketball|^volleyball|^tennis|^badminton|^golf|^bowling|^billiards|^pool_\(game\)|^table_tennis|^ping_pong|^hockey|^rugby|^cricket|^swimming$|^running_track|^track_and_field|^gymnastics|^figure_skating|^ice_skating|^skiing|^snowboard|^surfing|^surfboard|^boxing|^martial_arts|^karate|^judo|^kendo|^sumo|^wrestling|^fencing|^archery|^cycling|^sports|^sport$|^playing_sports|^racket|^bat_\(sports\)|^net$|^goal$|^trophy|^medal$|^jersey|^chess|^shogi|^go_\(board_game\)|^mahjong|^playing_card|^card$|^cards$|^tarot|^dice|^board_game|^video_game|^playing_games|^gaming|^arcade_|^crane_game|^jigsaw|^puzzle|^rubik|^jenga|^kendama|^yo-yo|^kite|^jump_rope|^hula_hoop|^frisbee|^water_gun|^toy_|^toy$|^game$|^gacha|^lottery|^pachinko|^slot_machine|^casino|^poker|^roulette"),
    ("物品", "其他物品", r"^book$|^books$|_book$|^book_|^open_book|^notebook|^diary|^paper$|_paper$|^paper_|^scroll$|^letter_|^envelope|^card$|^umbrella|^parasol|^bag$|_bag$|^bag_|^backpack|^handbag|^purse|^wallet|^suitcase|^luggage|^briefcase|^box$|_box$|^box_|^basket|^bucket|^barrel|^crate|^jar$|^bottle$|^vase|^candle|^lantern|^lamp|^torch$|^flashlight|^key$|^keys$|^lock$|^padlock|^chain$|^rope$|^string|^thread|^yarn|^needle|^scissors|^pen$|^pencil|^brush|^paintbrush|^palette|^easel|^canvas|^ruler|^eraser|^glue|^tape$|^stapler|^clipboard|^calendar_\(object\)|^map$|^globe$|^compass|^telescope|^binoculars|^magnifying_glass|^hourglass|^pocket_watch|^clock|^alarm_clock|^mirror|^comb$|^hairbrush|^towel|^soap|^toothbrush|^toothpaste|^shampoo|^cigarette|^cigar|^pipe$|^smoking_pipe|^lighter|^ashtray|^coin|^money|^banknote|^gold_bar|^treasure|^crystal$|^crystals|^orb$|^jewel$|^potion|^vial|^flask|^test_tube|^syringe|^pill$|^pills|^medicine|^bandage|^bandaid|^band-aid|^first_aid|^stethoscope|^doll$|_doll$|^dolls$|^stuffed_|^plush|^teddy_bear|^figure$|^figurine|^statue|^sculpture|^mask_\(object\)|^balloon|^gift|^present|^ribbon_\(object\)|^bell_\(object\)|^wind_chime|^fan$|^hand_fan|^folding_fan|^paper_fan|^uchiwa|^sensu|^flag$|^banner$|^sign$|^poster_\(object\)|^photo_\(object\)|^picture_frame|^frame_\(object\)|^trophy|^ticket|^charm_\(object\)|^omamori|^ofuda|^ema$|^tanzaku|^gohei|^rosary|^cross$|^bible|^grimoire|^spellbook|^tarot|^card_\(object\)|^ball_\(object\)|^cushion|^pillow|^blanket|^sleeping_bag|^tent|^bench|^ladder|^tool|_tool$|^wrench|^screwdriver|^hammer_\(tool\)|^saw$|^shovel|^pickaxe|^broom|^mop$|^vacuum|^trash|^garbage|^cardboard_box|^shopping_bag|^plastic_bag|^paper_bag|^bento_box|^watering_can|^hose$|^fishing_rod|^net_\(object\)|^cage$|^birdcage|^aquarium|^fishbowl|^snow_globe|^music_box|^jack-in-the-box|^rattle|^pacifier|^diaper|^bottle_\(baby\)|^cradle"),
]
RULES = [(g, s, re.compile(p)) for g, s, p in RULES]

# ---------- Danbooru tag-group sections ----------
# page -> default (大类, 子类) or None to ignore, plus [(heading substring, category)] checked first.
D = {
    "tag_group_accessories": (("服饰", "首饰·饰品"), [("Head", ("服饰", "帽子·头盔")), ("Neck", ("服饰", "领口·领带·颈饰"))]),
    "tag_group_artistic_license": (("其他", "未分类"), [("age", ("人物", "年龄")), ("hair", ("人物", "发型")), ("eyes", ("人物", "眼睛")), ("attire", ("服饰", "风格·时尚")), ("clothes", ("服饰", "风格·时尚")), ("body parts", ("人物", "身材"))]),
    "tag_group_ass": (("人物", "臀部"), [("hands", ("R18", "性行为")), ("heads", ("R18", "性行为")), ("cum", ("R18", "体液")), ("anus", ("R18", "性器官")), ("Misc", ("R18", "性癖·其他"))]),
    "tag_group_attire": (("服饰", "衣着状态"), [("Headwear", ("服饰", "帽子·头盔")), ("Shirts", ("服饰", "上衣")), ("Pants", ("服饰", "裤子")), ("Legs and Feet", ("服饰", "袜子·腿饰")), ("Shoes", ("服饰", "鞋子")), ("Uniforms", ("服饰", "制服·职业装")), ("Swimsuits", ("服饰", "泳装·紧身衣")), ("Traditional", ("服饰", "传统服饰")), ("Head and Face", ("服饰", "首饰·饰品")), ("Neck and Shoulders", ("服饰", "领口·领带·颈饰")), ("Limbs", ("服饰", "首饰·饰品")), ("Torso and Misc", ("服饰", "首饰·饰品")), ("Patterns", ("服饰", "花纹·材质")), ("Prints", ("服饰", "花纹·材质")), ("See also", ("服饰", "风格·时尚"))]),
    "tag_group_audio_tags": (("物品", "乐器·音乐"), [("Speakers and Headphones", ("物品", "电子设备")), ("Players", ("物品", "电子设备"))]),
    "tag_group_backgrounds": (("画面", "背景"), [("Background Related", ("镜头", "构图"))]),
    "tag_group_bdsm_and_torture": (("R18", "BDSM·束缚"), [("Beating", ("表情动作", "其他动作")), ("Marks", ("人物", "身体其他部位")),
                                   ("Psychological", ("表情动作", "表情")), ("Techniques", ("表情动作", "其他动作")), ("Torture", ("R18", "性癖·其他"))]),
    "tag_group_birds": (("物品", "动物"), [("Mythological", ("物品", "神话生物"))]),
    "tag_group_board_games": (("物品", "运动·游戏"), []),
    "tag_group_body_parts": (("人物", "身体其他部位"), [("Appendages", ("人物", "手·手臂"))]),
    "tag_group_breasts_tags": (("人物", "胸部"), [("Visib", ("R18", "裸露")), ("Clothes for breasts", ("服饰", "内衣")), ("Penis on", ("R18", "性行为")), ("Mouth on", ("R18", "性行为")), ("Hands on", ("R18", "性行为")), ("Toys on", ("R18", "情趣用品")), ("Docking", ("R18", "性行为"))]),
    "tag_group_cards": (("物品", "运动·游戏"), []),
    "tag_group_cats": (("物品", "动物"), [("Cat girls", ("人物", "种族·非人")), ("etymology", ("其他", "网络梗")), ("Behaviors", ("表情动作", "其他动作"))]),
    "tag_group_censorship": (("画面", "画质·元数据"), [("Explicit", ("R18", "裸露"))]),
    "tag_group_character_count": (("人物", "人数·性别"), [("Multiple views", ("镜头", "构图"))]),
    "tag_group_colors": (("画面", "颜色"), [("Techniques", ("画面", "艺术风格")), ("Filters", ("画面", "特效"))]),
    "tag_group_companies_and_brand_names": (("其他", "未分类"), [("Automotive", ("物品", "交通工具")), ("Clothing", ("服饰", "风格·时尚")), ("Musical", ("物品", "乐器·音乐")), ("Beverages", ("物品", "食物·饮料")), ("Foods", ("物品", "食物·饮料")), ("Restaurant", ("物品", "食物·饮料")), ("Defense", ("物品", "武器"))]),
    "tag_group_covering": (("表情动作", "手部动作"), []),
    "tag_group_dances": (("表情动作", "其他动作"), [("Meme", ("其他", "网络梗"))]),
    "tag_group_dogs": (("物品", "动物"), [("Dog girls", ("人物", "种族·非人")), ("etymology", ("R18", "体位")), ("Fantastical", ("物品", "神话生物"))]),
    "tag_group_doors_and_gates": (("场景", "家具·门窗"), [("Actions", ("表情动作", "其他动作"))]),
    "tag_group_ears_tags": (("人物", "耳朵"), [("Objects", ("服饰", "首饰·饰品")), ("Misc", ("表情动作", "手部动作"))]),
    "tag_group_eyes_tags": (("人物", "眼睛"), [("Pupils", ("人物", "瞳孔")), ("Emotions", ("表情动作", "表情")), ("closed", ("表情动作", "表情")), ("Stylistic", ("表情动作", "表情")), ("Accessories", ("服饰", "眼镜·面具")), ("Gazes", ("表情动作", "视线")), ("Actions", ("表情动作", "表情"))]),
    "tag_group_eyewear": (("服饰", "眼镜·面具"), [("Actions", ("表情动作", "手部动作"))]),
    "tag_group_face_tags": (("表情动作", "表情"), [("Sexual", ("R18", "性表情")), ("Drawing styles", ("人物", "面部")), ("Misc", ("人物", "面部")), ("Looking", ("表情动作", "视线")), ("Meme", ("其他", "网络梗"))]),
    "tag_group_family_relationships": (("人物", "身份·职业"), []),
    "tag_group_fashion_style": (("服饰", "风格·时尚"), [("Historical", ("服饰", "传统服饰")), ("Cultural", ("服饰", "传统服饰"))]),
    "tag_group_feet": (("人物", "腿·脚"), [("Poses", ("表情动作", "腿部动作")), ("Clothing", ("服饰", "袜子·腿饰")), ("Fetish", ("R18", "性癖·其他"))]),
    "tag_group_fighting_games": None,
    "tag_group_fine_art_parody": (("画面", "艺术风格"), []),
    "tag_group_fire": (("环境", "水·冰·火"), [("Body parts", ("人物", "翅膀·尾巴·角")), ("Objects", ("物品", "其他物品")), ("Weapons", ("物品", "武器"))]),
    "tag_group_flowers": (("环境", "植物·花"), []),
    "tag_group_focus_tags": (("镜头", "焦点"), []),
    "tag_group_food_tags": (("物品", "食物·饮料"), [("Professions", ("人物", "身份·职业")), ("Sexual", ("R18", "性癖·其他")), ("Actions", ("表情动作", "其他动作"))]),
    "tag_group_gender_nonconformity": (("人物", "人数·性别"), [("Fetishes", ("R18", "性癖·其他")), ("Anatomy", ("R18", "性器官"))]),
    "tag_group_gestures": (("表情动作", "手势"), []),
    "tag_group_groups": (("人物", "人数·性别"), []),
    "tag_group_hair": (("人物", "头发其他"), [("Facial hair", ("人物", "面部")), ("Accessories", ("服饰", "发饰")), ("hair care", ("物品", "其他物品")), ("Actions", ("表情动作", "手部动作"))]),
    "tag_group_hair_color": (("人物", "发色"), []),
    "tag_group_hair_styles": (("人物", "发型"), []),
    "tag_group_hands": (("表情动作", "手部动作"), [("another person", ("表情动作", "多人互动")), ("Hands on breasts", ("R18", "性行为")), ("Strange", ("人物", "手·手臂"))]),
    "tag_group_handwear": (("服饰", "手套"), [("Rings", ("服饰", "首饰·饰品")), ("Hand Accessories", ("服饰", "首饰·饰品")), ("Hand markings", ("人物", "妆容·纹身"))]),
    "tag_group_headwear": (("服饰", "帽子·头盔"), [("Not headwear", ("服饰", "发饰")), ("Actions", ("表情动作", "手部动作"))]),
    "tag_group_history": (("其他", "未分类"), []),
    "tag_group_holding_tags": (("表情动作", "拿着东西"), [("See Also", ("表情动作", "手部动作"))]),
    "tag_group_holidays_and_celebrations": (("环境", "季节·节日"), []),
    "tag_group_image_composition": (("镜头", "构图"), [("View Angle", ("镜头", "角度")), ("Perspective", ("镜头", "角度")), ("Format", ("画面", "媒介·格式")), ("Framing the body", ("镜头", "景别")), ("Subject matter", ("画面", "背景")), ("Styles", ("画面", "艺术风格")), ("Techniques", ("画面", "特效")), ("Patterns", ("服饰", "花纹·材质")), ("Flaws", ("画面", "画质·元数据"))]),
    "tag_group_japanese_dialects": (("画面", "文字·符号"), []),
    "tag_group_jobs": (("人物", "身份·职业"), [("Sexual", ("R18", "性癖·其他"))]),
    "tag_group_legendary_creatures": (("物品", "神话生物"), [("Miscellaneous", ("人物", "种族·非人"))]),
    "tag_group_legwear": (("服饰", "袜子·腿饰"), [("Action", ("表情动作", "手部动作"))]),
    "tag_group_lighting": (("画面", "光照"), [("Time of day", ("环境", "天气·时间"))]),
    "tag_group_locations": (("场景", "建筑"), [("Indoors", ("场景", "室内")), ("Natural", ("场景", "户外·自然")), ("Man-made", ("场景", "户外·城市")), ("Touhou", ("场景", "建筑")), ("Other", ("场景", "户外·城市"))]),
    "tag_group_makeup": (("人物", "妆容·纹身"), [("Objects", ("物品", "其他物品"))]),
    "tag_group_metatags": None,
    "tag_group_neck_and_neckwear": (("服饰", "领口·领带·颈饰"), [("Anatomy", ("人物", "身体其他部位")), ("Actions", ("表情动作", "手部动作")), ("Neckwear actions", ("表情动作", "手部动作"))]),
    "tag_group_nudity": (("服饰", "衣着状态"), [("Complete", ("R18", "裸露")), ("by gender", ("R18", "裸露")), ("Exposed breasts", ("R18", "裸露")), ("Exposed nipples", ("R18", "裸露")), ("ass or crotch", ("R18", "裸露")), ("exceptions", ("R18", "裸露")), ("Naughty", ("R18", "走光·偷窥")), ("Covering", ("表情动作", "手部动作")), ("Touching clothes", ("表情动作", "手部动作"))]),
    "tag_group_patterns": (("服饰", "花纹·材质"), []),
    "tag_group_people": (("人物", "身份·职业"), []),
    "tag_group_phrases": (("画面", "文字·符号"), [("Meme", ("其他", "网络梗"))]),
    "tag_group_pixiv_projects": None,
    "tag_group_platform_games": None,
    "tag_group_posture": (("表情动作", "基础姿势"), [("head", ("表情动作", "视线")), ("Arms", ("表情动作", "手臂动作")), ("Hand position", ("表情动作", "手部动作")), ("Hands touching", ("表情动作", "手部动作")), ("Legs", ("表情动作", "腿部动作")), ("Leg location", ("表情动作", "腿部动作")), ("Knee", ("表情动作", "腿部动作")), ("Foot", ("表情动作", "腿部动作")), ("two characters", ("表情动作", "多人互动")), ("three characters", ("表情动作", "多人互动")), ("Hugging", ("表情动作", "多人互动")), ("Carrying", ("表情动作", "多人互动"))]),
    "tag_group_prints": (("服饰", "花纹·材质"), []),
    "tag_group_pussy": (("R18", "性器官"), [("fluids", ("R18", "体液")), ("acts", ("R18", "性行为")), ("Hands on", ("R18", "性行为")), ("attire", ("R18", "色情服装"))]),
    "tag_group_real_world_locations": (("场景", "现实地点"), []),
    "tag_group_role-playing_games": None,
    "tag_group_sex_acts": (("R18", "性行为"), [("Fetishes", ("R18", "性癖·其他")), ("Cum Play", ("R18", "体液")), ("Facial Expressions", ("R18", "性表情")), ("Bondage", ("R18", "BDSM·束缚")), ("Exhibitionism", ("R18", "走光·偷窥")), ("Extreme", ("R18", "性癖·其他"))]),
    "tag_group_sex_objects": (("R18", "情趣用品"), [("BDSM", ("R18", "BDSM·束缚"))]),
    "tag_group_sexual_attire": (("R18", "色情服装"), [("Lingerie", ("服饰", "内衣")), ("BDSM", ("R18", "BDSM·束缚"))]),
    "tag_group_sexual_positions": (("R18", "体位"), [("Bondage", ("R18", "BDSM·束缚"))]),
    "tag_group_shooter_games": None,
    "tag_group_shoulders": (("服饰", "上衣"), [("Anatomy", ("人物", "身体其他部位")), ("Exposed", ("服饰", "衣着状态")), ("Hands", ("表情动作", "多人互动")), ("People touching", ("表情动作", "多人互动")), ("Animals", ("物品", "动物")), ("Objects", ("表情动作", "其他动作")), ("Misc", ("服饰", "衣着状态"))]),
    "tag_group_simulated_sex_acts": (("R18", "性行为"), []),
    "tag_group_skin_color": (("人物", "皮肤"), []),
    "tag_group_sleeves": (("服饰", "袖子"), [("Actions", ("表情动作", "手部动作"))]),
    "tag_group_sports": (("物品", "运动·游戏"), []),
    "tag_group_subjective": (("其他", "未分类"), []),
    "tag_group_symbols": (("画面", "文字·符号"), [("emotions", ("画面", "特效"))]),
    "tag_group_technology": (("物品", "电子设备"), [("Themes", ("画面", "艺术风格")), ("Robots", ("人物", "种族·非人")), ("Prosthetics", ("人物", "种族·非人")), ("Land Vehicles", ("物品", "交通工具")), ("Naval", ("物品", "交通工具")), ("Aerospace", ("物品", "交通工具")), ("Modern", ("服饰", "盔甲")), ("Futuristic", ("服饰", "盔甲")), ("Places", ("场景", "户外·城市")), ("Tools", ("物品", "其他物品")), ("Medical", ("物品", "其他物品")), ("Mecha", ("物品", "交通工具"))]),
    "tag_group_text": (("画面", "文字·符号"), [("metadata", ("画面", "画质·元数据")), ("Actions", ("表情动作", "其他动作"))]),
    "tag_group_theme": (("其他", "未分类"), []),
    "tag_group_transgender": (("人物", "人数·性别"), []),
    "tag_group_verbs_and_gerunds": (("表情动作", "其他动作"), []),
    "tag_group_video_game": (("物品", "运动·游戏"), [("Hardware", ("物品", "电子设备"))]),
    "tag_group_visual_aesthetic": (("画面", "艺术风格"), []),
    "tag_group_water": (("环境", "水·冰·火"), [("Wet", ("服饰", "衣着状态")), ("Clothes", ("服饰", "泳装·紧身衣")), ("Vehicles", ("物品", "交通工具")), ("Meteorology", ("环境", "天气·时间")), ("Geography", ("场景", "户外·自然"))]),
    "tag_group_wings": (("人物", "翅膀·尾巴·角"), [("Clothing", ("服饰", "首饰·饰品"))]),
    "tag_group_year_tags": (("画面", "画质·元数据"), []),
    "list_of_airplanes": (("物品", "交通工具"), [("Pilot gear", ("服饰", "制服·职业装")), ("Jobs", ("人物", "身份·职业"))]),
    "list_of_animals": (("物品", "动物"), []),
    "list_of_armor": (("服饰", "盔甲"), [("Personalities", ("人物", "身份·职业")), ("Shield", ("物品", "武器"))]),
    "list_of_car-related_tags": (("物品", "交通工具"), []),
    "list_of_game_activities": (("物品", "运动·游戏"), []),
    "list_of_ground_vehicles": (("物品", "交通工具"), [("Antivehicle", ("物品", "武器")), ("Jobs", ("人物", "身份·职业"))]),
    "list_of_playing_card_faces": (("物品", "运动·游戏"), []),
    "list_of_poses": (("表情动作", "基础姿势"), []),
    "list_of_ships": (("物品", "交通工具"), [("Weapon", ("物品", "武器")), ("Jobs", ("人物", "身份·职业"))]),
    "list_of_style_parodies": (("画面", "艺术风格"), []),
    "list_of_uniforms": (("服饰", "制服·职业装"), []),
    "list_of_weapons": (("物品", "武器"), [("Actions", ("表情动作", "其他动作"))]),
}
SERIES_ALIAS = {"舰队收藏": "舰队Collection", "火焰纹章": "火焰之纹章", "偶像大师灰姑娘女孩": "偶像大师 灰姑娘女孩", "Hololive": "hololive",
                "火焰之纹章 风花雪月": "火焰之纹章", "火焰之纹章 Engage": "火焰之纹章", "火焰之纹章if": "火焰之纹章", "火焰之纹章 if": "火焰之纹章"}
# Leftover general tags named after a series, e.g. vision_(genshin_impact).
SERIES_SUFFIX = re.compile(r"_\([^()]+\)$")
HEAD = re.compile(r"^h([1-6])(?:#[\w-]+)?\.\s*(.+?)\s*$")
LINK = re.compile(r"\[\[([^\]|#]+)")


def norm(t):
    return t.strip().lower().replace(" ", "_")


def load_groups(general):
    found = collections.defaultdict(list)
    for page, spec in D.items():
        path = os.path.join(GROUPS, page + ".json")
        if spec is None or not os.path.exists(path):
            continue
        default, overrides = spec
        head = ""
        for line in json.load(open(path, encoding="utf-8")).get("body", "").splitlines():
            m = HEAD.match(line.strip())
            if m:
                head = m.group(2) if int(m.group(1)) <= 4 else head.split(" / ")[0] + " / " + m.group(2)
                continue
            if not line.lstrip().startswith("*"):
                continue
            cat = next((c for key, c in overrides if key.lower() in head.lower()), default)
            for link in LINK.findall(line):
                t = norm(link)
                if t in general and cat not in found[t]:
                    found[t].append(cat)
    return found


# Costume / form notes that can sit in the last （） of a character's Chinese name instead of the series.
NOT_SERIES = re.compile(r"服装|再临|灵基|形态|泳装|私服|便服|皮肤|造型|衣装|ver|Ver|模式|版$|少年|幼年|成年|女性|男性|^女$|^男$")


def series_of(zh):
    # The translation table names characters as 名字（作品）.
    for name in reversed(re.findall(r"（([^（）]+)）", zh)):
        if not NOT_SERIES.search(name):
            return re.sub(r"[_\s]+", " ", name).strip()
    return None


def simplified(alias):
    # Kanji like 長髪 are not in GB2312, 长发 is.
    if KANA.search(alias):
        return False
    try:
        "".join(HAN.findall(alias)).encode("gb2312")
        return True
    except UnicodeEncodeError:
        return False


def classify(tag):
    if R18_WORDS.search(tag):
        return "R18", next(n for n, p in R18_SUB if p.search(tag))
    for g, s, p in RULES:
        if p.search(tag):
            return g, s
    return None


def main():
    rows = [r for r in csv.reader(open(SRC, encoding="utf-8")) if len(r) >= 4]
    general = {r[0] for r in rows if r[1] == "0"}
    dan = load_groups(general)

    cats = collections.defaultdict(list)
    for tag, cat, cnt, aliases in rows:
        al = aliases.split(",") if aliases else []
        ban = 2 if any(a.startswith(BAN) for a in al) else 1 if any(a.startswith(WARN) for a in al) else 0
        han = [a for a in al if HAN.search(a)]
        # Japanese aliases also contain kanji: prefer simplified Chinese, then anything without kana.
        zh = next((a for a in han if simplified(a)), next((a for a in han if not KANA.search(a)), han[0] if han else ""))
        # Other names (Chinese, Japanese, romaji) only for search, markers stripped.
        others = [x.replace(BAN, "").replace(WARN, "") for x in al if x != zh][:MAX_ALIASES]
        item = [tag, zh, int(cnt), ban, ",".join(others).lower()]
        if cat == "4":
            key = series_of(zh)
            cats[("角色", SERIES_ALIAS.get(key, key) or "其他角色")].append(item)
        elif cat == "3":
            cats[("作品", "全部作品")].append(item)
        else:
            c = classify(tag) or (dan[tag][0] if dan.get(tag) else None)
            c = c or (("其他", "作品相关") if SERIES_SUFFIX.search(tag) else ("其他", "未分类"))
            cats[c].append(item)

    # Small character series fold into 其他角色.
    for (g, s) in list(cats):
        if g == "角色" and s != "其他角色" and len(cats[(g, s)]) < 30:
            cats[("角色", "其他角色")] += cats.pop((g, s))
    role_subs = sorted((s for g, s in cats if g == "角色" and s != "其他角色"),
                       key=lambda s: -sum(i[2] for i in cats[("角色", s)]))
    ORDER["角色"] = role_subs + ["其他角色"]

    groups = []
    for g, subs in ORDER.items():
        out_subs = []
        for s in subs:
            items = sorted(cats.pop((g, s), []), key=lambda i: -i[2])
            if items:
                out_subs.append({"name": s, "tags": items})
        groups.append({"name": g, "subs": out_subs})
    assert not cats, f"categories missing from ORDER: {list(cats)}"

    data = {
        "说明": "中文标签词库。tags 每项为 [英文标签, 中文, Danbooru 图片数, 违禁级别, 其他别名（仅供搜索）]。"
                "违禁级别 2 = 🚫绝对禁用（任何时候都不准写进正向提示词），1 = ⚠仅全年龄（正向出现 nsfw/explicit/sensitive 时不准用），0 = 可用。"
                "违禁词的中文前面也带有对应标记。",
        "groups": groups,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    for grp in groups:
        print(grp["name"], sum(len(s["tags"]) for s in grp["subs"]), " ".join(f'{s["name"]}({len(s["tags"])})' for s in grp["subs"]))
    print("->", OUT)


main()
