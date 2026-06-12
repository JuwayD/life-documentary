"""Yangzhou expanded districts for Phase 5A."""
from mingrpg.core.world import World


LOCATIONS = [
    {
        "id": "academy_gate",
        "name": "崇文书院门口",
        "type": "outdoor_scholarly",
        "size": [14, 12],
        "exits": {"west": "street_main", "north": "academy_hall"},
        "tags": ["public", "scholarly", "quiet"],
        "description": "粉墙黛瓦间一座木牌坊高立,上书'崇文书院'。门前槐影婆娑,偶有青衿学子捧书而过。",
    },
    {
        "id": "academy_hall",
        "name": "书院讲堂",
        "type": "indoor_scholarly",
        "size": [12, 10],
        "exits": {"south": "academy_gate", "east": "academy_library"},
        "tags": ["scholarly", "social"],
        "description": "讲堂内木案成列,墙上挂着朱子格言。窗外竹影摇曳,案头墨香未散。",
    },
    {
        "id": "academy_library",
        "name": "藏书楼",
        "type": "indoor_private",
        "size": [10, 10],
        "exits": {"west": "academy_hall"},
        "tags": ["scholarly", "private", "quiet"],
        "description": "楼中书架高耸,经史子集分门别类。楼梯吱呀作响,角落里锁着几只旧书箱。",
    },
    {
        "id": "clinic_front",
        "name": "回春堂门面",
        "type": "outdoor_commercial",
        "size": [12, 10],
        "exits": {"east": "market_gate", "north": "clinic_hall"},
        "tags": ["public", "commercial", "medicine"],
        "description": "门前悬着葫芦招牌,药香从帘内透出。台阶旁排着几名候诊百姓。",
    },
    {
        "id": "clinic_hall",
        "name": "回春堂诊室",
        "type": "indoor_commercial",
        "size": [10, 8],
        "exits": {"south": "clinic_front"},
        "tags": ["commercial", "medicine", "quiet"],
        "description": "诊室一侧是药柜,抽屉上贴着细小药名。脉枕、银针、药秤摆在案上。",
    },
    {
        "id": "river_dock",
        "name": "运河码头",
        "type": "outdoor",
        "size": [24, 16],
        "exits": {"west": "market_gate", "south": "ferry_pier", "east": "warehouse"},
        "tags": ["public", "commercial", "dock", "crowded"],
        "description": "运河水色浑黄,船桅林立。脚夫扛包奔走,牙行伙计高声点货。",
    },
    {
        "id": "ferry_pier",
        "name": "渡口",
        "type": "outdoor",
        "size": [14, 10],
        "exits": {"north": "river_dock"},
        "tags": ["public", "dock", "travel"],
        "description": "一条木栈道伸向河面,乌篷小船随水轻晃。船夫们靠在桩旁等客。",
    },
    {
        "id": "warehouse",
        "name": "码头货栈",
        "type": "indoor_commercial",
        "size": [16, 12],
        "exits": {"west": "river_dock"},
        "tags": ["commercial", "dock", "private"],
        "description": "货栈里堆满麻袋、木箱和油布包。账房桌边挂着一串铜锁,空气里有潮湿稻谷味。",
    },
    {
        "id": "temple_gate",
        "name": "城隍庙前",
        "type": "outdoor_religious",
        "size": [16, 12],
        "exits": {"east": "street_main", "north": "temple_hall"},
        "tags": ["public", "religious", "social"],
        "description": "庙前香客往来,卖香烛和糖人的小贩沿墙排开。石狮口中塞着褪色红绸。",
    },
    {
        "id": "temple_hall",
        "name": "城隍庙大殿",
        "type": "indoor_religious",
        "size": [12, 10],
        "exits": {"south": "temple_gate"},
        "tags": ["religious", "quiet"],
        "description": "殿中城隍神像端坐,香烟缭绕。功德箱旁的木牌写着祈福、还愿、问签的规矩。",
    },
]


STORY_SEEDS = {
    "main_thread": {
        "id": "petition_against_bully",
        "title": "状告漕帮恶霸",
        "premise": "玩家手中状纸控告街市地痞赵三勾结码头势力欺压寒士,但案情背后牵连码头货栈、府衙幕僚与豪商账目。",
        "current_pressure": "王知府想草草打发,刘师爷暗中观望,真正证人散在街市、码头和书院。",
        "initial_leads": [
            {"location": "court_hall", "entity": "shiye", "clue": "刘师爷知道状纸是否会被正式收案"},
            {"location": "market_gate", "entity": "beggar_liu", "clue": "乞丐老刘见过恶霸赵三与货栈伙计夜谈"},
            {"location": "river_dock", "entity": "dock_boss_qian", "clue": "钱把头知道赵三替谁压价收货"},
            {"location": "academy_hall", "entity": "teacher_gu", "clue": "顾先生保存着一份旧案抄本"},
        ],
        "open_questions": [
            "赵三究竟替谁办事?",
            "府衙为何不愿认真受理此案?",
            "玩家能否找到愿意出面作证的人?",
            "状纸之外是否还有账簿、药单、船货记录等实证?",
        ],
        "pressure_clocks": [
            {"id": "witness_pressure", "name": "证人受压", "value": 0, "danger_at": 3},
            {"id": "official_patience", "name": "府衙耐心", "value": 0, "danger_at": 4},
        ],
    },
    "side_threads": [
        {
            "id": "academy_missing_book",
            "title": "藏书楼失书",
            "hook": "藏书楼少了一册载有旧案批注的地方志,林生员怕被诬为窃书。",
            "anchors": [{"location": "academy_library"}, {"entity": "student_lin"}, {"entity": "teacher_gu"}],
            "stakes": "若找回失书,可补强主线旧案线索;若处置失当,书院会对玩家关门。",
        },
        {
            "id": "clinic_debtors",
            "title": "病人欠账",
            "hook": "回春堂药材涨价,何郎中怀疑有人囤药逼债。",
            "anchors": [{"location": "clinic_hall"}, {"entity": "doctor_he"}, {"entity": "herb_apprentice"}],
            "stakes": "医馆能提供验伤与药单证据,但卷入纠纷会得罪药商。",
        },
        {
            "id": "warehouse_shortage",
            "title": "货栈少货",
            "hook": "码头货栈账上少了三袋米,脚夫们互相猜疑。",
            "anchors": [{"location": "warehouse"}, {"entity": "dock_boss_qian"}, {"entity": "porter_niu"}],
            "stakes": "查明短货可换来码头证言,也可能触出私运线索。",
        },
        {
            "id": "night_ferry_secret",
            "title": "夜渡私语",
            "hook": "周船夫夜里渡过一名蒙面客,对方丢下一枚官府火漆碎片。",
            "anchors": [{"location": "ferry_pier"}, {"entity": "boatman_zhou"}],
            "stakes": "夜间追查可能触犯夜禁,但能接上府衙暗线。",
        },
        {
            "id": "temple_donation_box",
            "title": "功德箱短少",
            "hook": "城隍庙功德箱少钱,庙祝沈老怀疑并非普通偷儿。",
            "anchors": [{"location": "temple_hall"}, {"entity": "temple_keeper"}],
            "stakes": "庙前香客众多,容易发酵成舆论,也能牵出密约。",
        },
        {
            "id": "food_stall_credit",
            "title": "小吃摊赊账",
            "hook": "孙老四被迫给某些人记空账,账尾写着奇怪记号。",
            "anchors": [{"location": "market_stall_food"}, {"entity": "vendor_food"}, {"entity": "student_lin"}],
            "stakes": "账本可揭示街市勒索链,但摊主怕报复。",
        },
        {
            "id": "fabric_fake_brocade",
            "title": "云锦真假",
            "hook": "周掌柜的云锦价格离谱,行商说其中一匹可能是赃物。",
            "anchors": [{"location": "market_stall_fabric"}, {"entity": "vendor_fabric"}, {"entity": "traveling_merchant"}],
            "stakes": "买卖纠纷可演变为商业案,也能引出豪商网络。",
        },
        {
            "id": "teahouse_storyteller",
            "title": "茶楼说书",
            "hook": "悦来茶楼说书人把近来的官司编进段子,引来捕快侧目。",
            "anchors": [{"location": "teahouse"}, {"entity": "teahouse_owner"}, {"entity": "constable"}],
            "stakes": "茶楼消息快,但流言会改变 NPC 态度。",
        },
        {
            "id": "inn_missing_traveler",
            "title": "客栈失客",
            "hook": "悦来客栈有客人留下路引后失踪,店小二记得他问过货栈路。",
            "anchors": [{"location": "inn_hall"}, {"entity": "innkeeper"}, {"entity": "inn_waiter"}],
            "stakes": "客栈线索可通向码头,也可能暴露玩家行踪。",
        },
        {
            "id": "constable_dilemma",
            "title": "捕快两难",
            "hook": "李捕快奉命压住街市纷争,却私下认为案中有冤。",
            "anchors": [{"location": "market_street"}, {"entity": "constable"}],
            "stakes": "若取得信任,捕快可成为制度内助力;若触怒他,巡查压力上升。",
        },
        {
            "id": "court_yard_secret",
            "title": "府衙密议",
            "hook": "衙役私下议论状纸已被师爷压下,暗示府衙内部有人不希望案子被受理。",
            "anchors": [{"location": "court_yard"}, {"entity": "guard_a"}, {"entity": "guard_b"}],
            "stakes": "偷听衙役对话可获知府衙内部分歧,但被发觉可能以窥探官府论处。",
        },
        {
            "id": "street_main_rumor",
            "title": "漕帮暗货",
            "hook": "路人传言漕帮在码头新到一批货,运货时辰避人耳目,不走常路。",
            "anchors": [{"location": "street_main"}, {"entity": "beggar_liu"}, {"entity": "dock_boss_qian"}],
            "stakes": "追查这批暗货可揭开走私链,但惊动漕帮会直接推高证人受压钟。",
        },
    ],
    "emergent_guidance": [
        "这些是可供 GM 组合的素材,不是必须完成的任务清单。",
        "支线是否出现、如何推进、是否并入主线,由玩家行动、NPC 性格、近期事件和掷骰共同决定。",
        "推进任何线索时用 set_flag/log_event/add_memory 记录已发现事实和 NPC 态度,不要在代码层判断完成条件。",
    ],
}

ENDING_SEEDS = [
    {
        "id": "official_vindication",
        "title": "公堂昭雪",
        "trigger_hint": "证据链充足、证人愿意出面且府衙压力未失控时,可让官府正式受理并惩办恶霸。",
        "outcome_hint": "玩家获得清白与民望,但会得罪码头豪强。",
    },
    {
        "id": "private_settlement",
        "title": "私下和解",
        "trigger_hint": "证据不足但已掌握可谈判筹码,且顾问或中间人愿意斡旋时。",
        "outcome_hint": "赔偿与息事宁人并存,真凶可能仍在暗处。",
    },
    {
        "id": "exile_from_yangzhou",
        "title": "远走扬州",
        "trigger_hint": "证人受压、府衙耐心耗尽或玩家触怒权势者后,可选择保命离城。",
        "outcome_hint": "主线以失败或未竟收束,留下日后翻案余地。",
    },
]


ENTITIES = [
    {
        "id": "teacher_gu",
        "name": "顾先生",
        "type": "npc",
        "location": "academy_hall",
        "pos": [5, 4],
        "attributes": {
            "hp": 55, "max_hp": 55, "rank": "生员",
            "occupation": "书院先生",
            "personality": "清正迂直,重名节,对落魄读书人多有怜惜",
            "is_advisor": True,
            "advisor_topics": ["讼状", "旧案", "读书人关系"],
            "advisor_style": "循循善诱,引经据典,但不谙官场实务",
            "skills_taught": ["litigation", "calligraphy"],
            "attack": 1, "defense": 9, "money_wen": 120,
            "price_list": {"annotated_classics": 80, "copy_service": 30},
            "service_catalog": {
                "copy_writing": {"name": "代写讼状", "price_wen": 50},
                "tutoring": {"name": "讲学授课", "price_wen": 20},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "这位学子,来书院有何贵干?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。坐,今日讲《论语》。", "min_attitude": 20, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "academy", "label": "书院之事", "unlock_attitude": -20, "lines": [
                        {"text": "书院近来不太平,藏书楼丢了一册地方志,林生员怕被诬为窃书。", "min_attitude": 0, "max_attitude": 100},
                    ]},
                    {"id": "old_case", "label": "旧案文书", "unlock_attitude": 20, "lines": [
                        {"text": "老夫保存着一份旧案抄本,上面有知府的批注。你若要查案,可来借阅。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "litigation_advice", "label": "讼学指点", "unlock_attitude": 10, "lines": [
                        {"text": "写状纸讲究格式与措辞。你要告人,须得有理有据,不可意气用事。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。读书人当以天下为己任。", "min_attitude": -100, "max_attitude": 100},
                ],
                "special": [
                    {"trigger": "first_meeting", "text": "你是来求学的?嗯,看你面相,倒是个有志气的。坐吧。"},
                ],
            },
            "rumor_hooks": ["书院失窃", "乡试舞弊传闻", "旧案文书"],
        },
        "status_effects": [],
        "inventory": [{"id": "annotated_classics", "name": "批注经书", "qty": 1}],
        "tags": ["commoner", "scholarly", "teacher"],
    },
    {
        "id": "student_lin",
        "name": "林生员",
        "type": "npc",
        "location": "academy_library",
        "pos": [4, 5],
        "attributes": {
            "hp": 45, "max_hp": 45, "rank": "生员",
            "occupation": "书院学生",
            "personality": "心高气傲,口快心软,常因家贫受同窗轻慢",
            "attack": 1, "defense": 8, "money_wen": 18,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "你也是来借书的?藏书楼在那边。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。今日抄了不少,分你看看。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "missing_book", "label": "失书之事", "unlock_attitude": 0, "lines": [
                        {"text": "那册地方志不见了,他们怀疑是我拿的。可我真没拿!", "min_attitude": 0, "max_attitude": 100},
                        {"text": "钥匙在我手上,所以他们第一个就怀疑我。但钥匙不止我一个人有。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                    {"id": "poverty", "label": "贫寒之苦", "unlock_attitude": 10, "lines": [
                        {"text": "唉,家贫买不起书,只好来抄。同窗们看不起我,但我不在乎。", "min_attitude": 10, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走。若找到那册书,请告诉我。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "schedule": {
                "巳时": {"location": "academy_library", "pos": [4, 5], "activity": "在藏书楼抄书"},
                "午时": {"location": "market_stall_food", "pos": [2, 2], "activity": "在小吃摊赊一碗热汤"},
                "酉时": {"location": "academy_hall", "pos": [7, 5], "activity": "回讲堂温书"},
            },
            "rumor_hooks": ["贫寒学子", "赊账", "藏书楼钥匙"],
        },
        "status_effects": [],
        "inventory": [{"id": "copied_notes", "name": "抄书札记", "qty": 1}],
        "tags": ["commoner", "scholarly", "student"],
    },
    {
        "id": "doctor_he",
        "name": "何郎中",
        "type": "npc",
        "location": "clinic_hall",
        "pos": [5, 3],
        "attributes": {
            "hp": 55, "max_hp": 55, "rank": "平民",
            "occupation": "医馆郎中",
            "personality": "谨慎仁厚,诊病细致,不愿卷入官司但厌恶欺压病患",
            "skills_taught": ["medicine"],
            "attack": 1, "defense": 9, "money_wen": 260,
            "price_list": {"herb_bundle": 12},
            "service_catalog": {
                "diagnosis": {"name": "问诊开方", "price_wen": 15},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "请坐。哪里不舒服?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。今日气色不错。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "medicine", "label": "问诊开方", "unlock_attitude": -20, "lines": [
                        {"text": "伸出舌头让我看看。嗯……有些虚火,我给你开副清热的方子。", "min_attitude": -20, "max_attitude": 100},
                    ]},
                    {"id": "clinic_secrets", "label": "医馆之事", "unlock_attitude": 15, "lines": [
                        {"text": "最近药材涨价涨得厉害,我怀疑有人在囤药逼债。", "min_attitude": 15, "max_attitude": 100},
                        {"text": "码头那边常有伤患来看病,有些伤不像干活弄的。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "多休息,按时服药。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "schedule": {
                "卯时": {"location": "clinic_front", "pos": [6, 4], "activity": "开门晒药"},
                "巳时": {"location": "clinic_hall", "pos": [5, 3], "activity": "坐堂问诊"},
                "午时": {"location": "clinic_hall", "pos": [5, 3], "activity": "为病患复诊"},
                "酉时": {"location": "temple_gate", "pos": [5, 6], "activity": "去庙前义诊"},
            },
            "rumor_hooks": ["药材涨价", "码头伤患", "疫病传言"],
        },
        "status_effects": [],
        "inventory": [
            {"id": "herb_bundle", "name": "草药包", "qty": 8},
            {"id": "silver_needles", "name": "银针", "qty": 1},
        ],
        "tags": ["commoner", "doctor", "medicine"],
    },
    {
        "id": "herb_apprentice",
        "name": "药童阿七",
        "type": "npc",
        "location": "clinic_front",
        "pos": [3, 4],
        "attributes": {
            "hp": 35, "max_hp": 35, "rank": "平民",
            "occupation": "医馆药童",
            "personality": "机灵嘴甜,跑腿极快,知道许多病人家长里短",
            "attack": 1, "defense": 8, "money_wen": 12,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "客官抓药还是看病?郎中在里面。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来啦!今日药齐了,我给你包好。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "patients", "label": "病人之事", "unlock_attitude": 0, "lines": [
                        {"text": "最近来看病的人不少,好多都是码头上的。", "min_attitude": 0, "max_attitude": 100},
                        {"text": "（小声）有些病人欠着账呢,何郎中心善,不好意思催。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "慢走!按时吃药啊!", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": ["药材短缺", "病人欠账"],
        },
        "status_effects": [],
        "inventory": [{"id": "medicine_scale", "name": "药秤", "qty": 1}],
        "tags": ["commoner", "medicine", "apprentice"],
    },
    {
        "id": "dock_boss_qian",
        "name": "钱把头",
        "type": "npc",
        "location": "river_dock",
        "pos": [12, 8],
        "attributes": {
            "hp": 75, "max_hp": 75, "rank": "平民",
            "occupation": "码头脚夫把头",
            "personality": "粗豪精明,讲义气也看钱,对货栈账目颇有门道",
            "attack": 4, "defense": 11, "weapon_damage": "1d6", "weapon_name": "扁担",
            "money_wen": 180,
            "service_catalog": {
                "hire_porter": {"name": "雇脚夫搬运", "price_wen": 15},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "干什么的?码头重地,闲人免进。", "min_attitude": -100, "max_attitude": 0},
                    {"text": "哦,是你。有什么活?", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "dock_work", "label": "码头之事", "unlock_attitude": 0, "lines": [
                        {"text": "码头上的事,你少打听。我只管搬货,别的不知道。", "min_attitude": -50, "max_attitude": 10},
                        {"text": "（压低声音）货栈少了三袋米,账房说是脚夫偷的。我信不过。", "min_attitude": 15, "max_attitude": 100},
                        {"text": "赵三?他替人收货,给的价低得很。但没人敢不卖。", "min_attitude": 25, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "行了,有活找我。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "schedule": {
                "卯时": {"location": "river_dock", "pos": [12, 8], "activity": "清点早船货物"},
                "午时": {"location": "warehouse", "pos": [7, 5], "activity": "与账房核对货单"},
                "酉时": {"location": "teahouse", "pos": [6, 6], "activity": "在茶楼听消息"},
            },
            "rumor_hooks": ["漕运短缺", "货栈少货", "脚夫械斗"],
        },
        "status_effects": [],
        "inventory": [{"id": "shoulder_pole", "name": "扁担", "qty": 1}],
        "tags": ["commoner", "dock_worker", "informant"],
    },
    {
        "id": "porter_niu",
        "name": "牛脚夫",
        "type": "npc",
        "location": "river_dock",
        "pos": [9, 9],
        "attributes": {
            "hp": 65, "max_hp": 65, "rank": "平民",
            "occupation": "码头脚夫",
            "personality": "憨直少言,力气很大,最怕拖欠工钱",
            "attack": 3, "defense": 10, "money_wen": 25,
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "……", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你来了。要搬什么?", "min_attitude": 10, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "dock_work", "label": "码头之事", "unlock_attitude": 5, "lines": [
                        {"text": "我不爱说话。但你要是问夜船的事……我见过。", "min_attitude": 5, "max_attitude": 100},
                        {"text": "工钱又拖了。钱把头说是账房的问题,我不信。", "min_attitude": 15, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "……", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": ["拖欠工钱", "夜船卸货"],
        },
        "status_effects": [],
        "inventory": [{"id": "rope", "name": "麻绳", "qty": 1}],
        "tags": ["commoner", "dock_worker"],
    },
    {
        "id": "boatman_zhou",
        "name": "周船夫",
        "type": "npc",
        "location": "ferry_pier",
        "pos": [6, 5],
        "attributes": {
            "hp": 55, "max_hp": 55, "rank": "平民",
            "occupation": "渡船船夫",
            "personality": "沉默谨慎,熟悉水路,夜里见过不少不该见的事",
            "attack": 2, "defense": 9, "money_wen": 70,
            "service_catalog": {
                "ferry_crossing": {"name": "摆渡过河", "price_wen": 5},
                "night_ferry": {"name": "夜间摆渡", "price_wen": 20},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "要过河?上来吧。", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你又来了。今日风浪小,走吧。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "river_news", "label": "河上之事", "unlock_attitude": 5, "lines": [
                        {"text": "我不爱多嘴。但河上的事,我看得清楚。", "min_attitude": 5, "max_attitude": 100},
                        {"text": "有次夜里渡过一名蒙面客,丢下一枚官府火漆碎片。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "night_ferry", "label": "夜渡之事", "unlock_attitude": 20, "lines": [
                        {"text": "夜间摆渡?不是不行,但得加钱。而且……有些事你最好别问。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "到了。下船小心。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": ["夜渡", "失踪货船", "水路私运"],
        },
        "status_effects": [],
        "inventory": [{"id": "boat_hook", "name": "撑船篙", "qty": 1}],
        "tags": ["commoner", "boatman", "traveler"],
    },
    {
        "id": "temple_keeper",
        "name": "庙祝沈老",
        "type": "npc",
        "location": "temple_hall",
        "pos": [6, 4],
        "attributes": {
            "hp": 50, "max_hp": 50, "rank": "平民",
            "occupation": "城隍庙庙祝",
            "personality": "慢条斯理,说话玄虚,记得许多城中旧事和香客愿文",
            "attack": 1, "defense": 9, "money_wen": 90,
            "price_list": {"incense": 3, "candle_pair": 5, "fortune_paper": 2},
            "service_catalog": {
                "blessing": {"name": "祈福法事", "price_wen": 30},
                "fortune_sticks": {"name": "求签问卦", "price_wen": 10},
            },
            "memories": [],
            "dialogue_lines": {
                "greetings": [
                    {"text": "施主,来上香还是求签?", "min_attitude": -100, "max_attitude": 100},
                    {"text": "你又来了。城隍爷会保佑你的。", "min_attitude": 15, "max_attitude": 100},
                ],
                "topics": [
                    {"id": "temple_matters", "label": "庙中之事", "unlock_attitude": 0, "lines": [
                        {"text": "功德箱最近少了钱。我怀疑不是普通偷儿。", "min_attitude": 10, "max_attitude": 100},
                        {"text": "旧案?城隍庙里供着许多冤魂牌位。有些事,老夫记得。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                    {"id": "visitor_secrets", "label": "香客之事", "unlock_attitude": 20, "lines": [
                        {"text": "（捋须）常有香客在殿中密约。老夫虽老,耳朵不聋。", "min_attitude": 20, "max_attitude": 100},
                    ]},
                ],
                "farewells": [
                    {"text": "去吧。心诚则灵。", "min_attitude": -100, "max_attitude": 100},
                ],
            },
            "rumor_hooks": ["旧案冤魂", "功德箱短少", "香客密约"],
        },
        "status_effects": [],
        "inventory": [{"id": "fortune_sticks", "name": "签筒", "qty": 1}],
        "tags": ["commoner", "religious", "informant"],
    },
]


def _merge_exits(world: World, location_id: str, exits: dict) -> None:
    loc = world.get_location(location_id)
    if loc is None:
        return
    loc.setdefault("exits", {}).update(exits)
    world.save_location(loc)


def _merge_schedule(world: World, entity_id: str, schedule: dict) -> None:
    entity = world.get_entity(entity_id)
    if entity is None:
        return
    entity.setdefault("attributes", {}).setdefault("schedule", {}).update(schedule)
    world.save_entity(entity)


def seed_yangzhou_districts(world: World) -> None:
    """Populate expanded Yangzhou districts for Phase 5A."""
    _merge_exits(world, "street_main", {
        "east": "academy_gate",
        "west": "temple_gate",
    })
    _merge_exits(world, "market_gate", {
        "west": "clinic_front",
        "east": "river_dock",
    })

    for location in LOCATIONS:
        world.save_location(location)

    for entity in ENTITIES:
        world.save_entity(entity)

    _merge_schedule(world, "constable", {
        "巳时": {"location": "market_street", "pos": [15, 15], "activity": "巡查街市"},
        "午时": {"location": "teahouse", "pos": [4, 4], "activity": "在茶楼打听纠纷"},
        "酉时": {"location": "court_yard", "pos": [10, 8], "activity": "回府衙交差"},
    })
    _merge_schedule(world, "inn_waiter", {
        "巳时": {"location": "inn_hall", "pos": [10, 7], "activity": "招呼客人"},
        "午时": {"location": "market_street", "pos": [18, 12], "activity": "替客栈采买"},
        "酉时": {"location": "inn_hall", "pos": [9, 6], "activity": "准备晚饭"},
    })
    _merge_schedule(world, "vendor_food", {
        "卯时": {"location": "market_stall_food", "pos": [3, 3], "activity": "支起小吃摊"},
        "午时": {"location": "market_stall_food", "pos": [3, 3], "activity": "招呼午饭客人"},
        "酉时": {"location": "market_gate", "pos": [5, 6], "activity": "收摊回家"},
    })

    _attach_story_seeds(world)
    world.set_flag("phase5a_world_expanded", True)
    world.set_flag("story_seeds", STORY_SEEDS)
    world.set_flag("ending_seeds", ENDING_SEEDS)
    world.set_flag("phase5bc_story_materials", True)

    # ---- Merge evolution registry for key NPCs ----
    registry = world.get_flag("evolution_registry") or []
    existing_ids = {e["entity_id"] for e in registry}
    new_entries = [
        {"entity_id": "student_lin", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "有日程,与藏书楼失书支线相关"},
        {"entity_id": "doctor_he", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "有日程,医馆可提供验伤证据"},
        {"entity_id": "dock_boss_qian", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "有日程,码头主线关键证人"},
        {"entity_id": "constable", "frequency": "every_2_turns",
         "last_evolved_turn": 0, "reason": "有日程,捕快两难支线核心"},
        {"entity_id": "inn_waiter", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "有日程,客栈失客支线相关"},
        {"entity_id": "vendor_food", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "有日程,小吃摊赊账支线相关"},
        {"entity_id": "teacher_gu", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "顾问NPC,书院支线相关"},
        {"entity_id": "boatman_zhou", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "夜渡支线相关"},
        {"entity_id": "temple_keeper", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "功德箱支线相关"},
        {"entity_id": "beggar_liu", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "街市消息灵通"},
        {"entity_id": "vendor_fabric", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "云锦真假支线相关"},
        {"entity_id": "teahouse_owner", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "茶楼说书支线相关"},
        {"entity_id": "innkeeper", "frequency": "every_5_turns",
         "last_evolved_turn": 0, "reason": "客栈失客支线相关"},
        {"entity_id": "traveling_merchant", "frequency": "dormant",
         "last_evolved_turn": 0, "reason": "行商,云锦支线触发时激活"},
    ]
    for entry in new_entries:
        if entry["entity_id"] not in existing_ids:
            registry.append(entry)
    world.set_flag("evolution_registry", registry)


def _attach_story_seeds(world: World) -> None:
    for lead in STORY_SEEDS["main_thread"]["initial_leads"]:
        entity_id = lead.get("entity")
        if entity_id:
            _append_unique_hook(world, entity_id, lead["clue"])

    for thread in STORY_SEEDS["side_threads"]:
        for anchor in thread["anchors"]:
            entity_id = anchor.get("entity")
            if entity_id:
                _append_unique_hook(world, entity_id, thread["hook"])
            location_id = anchor.get("location")
            if location_id:
                _append_location_thread(world, location_id, thread)


def _append_unique_hook(world: World, entity_id: str, hook: str) -> None:
    entity = world.get_entity(entity_id)
    if entity is None:
        return
    hooks = entity.setdefault("attributes", {}).setdefault("rumor_hooks", [])
    if hook not in hooks:
        hooks.append(hook)
    world.save_entity(entity)


def _append_location_thread(world: World, location_id: str, thread: dict) -> None:
    location = world.get_location(location_id)
    if location is None:
        return
    threads = location.setdefault("story_threads", [])
    if not any(t.get("id") == thread["id"] for t in threads):
        threads.append({
            "id": thread["id"],
            "title": thread["title"],
            "hook": thread["hook"],
            "stakes": thread["stakes"],
        })
    world.save_location(location)
