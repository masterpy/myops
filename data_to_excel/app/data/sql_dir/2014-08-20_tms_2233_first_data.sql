SELECT
d.dept_manage_area_name AS GuanLiQuYu,
jrc.class_campus_name AS FenXiao,
jrc.class_gt_name NianBu,
jrc.class_grade_name NianJi,
jrc.class_subject_name Xueke,
jrc.class_profit_name LiRun,
jrc.class_no AS BanHao,
jrc.class_name AS BanMing,
jrc.class_year NianFen,
jrc.class_season_name 季节,
jrc.class_total_num 总课次,
jrc.class_past_num 已上课次,
case jrc.class_status when 0 then '未开班' when 1 then '开班' when 2 then '强制开班' when 3 then '停班' when 4 then '结课' end 班级状态,
jrc.class_week_text AS 周表,
jrc.class_start_time AS 上课时间,
jrc.class_teacher_name AS 教师,
jrc.class_confirm_num 已报人数,
count(qq.sid) 升秋人次,
count(distinct qq.sid) 升秋人数
FROM tb_jrclass jrc
INNER JOIN tb_regist reg on reg.reg_class_id = jrc.class_id
INNER JOIN tb_department d on d.dept_id = jrc.class_campus_id
left join (
select r1.reg_student_id sid from tb_regist r1 join tb_jrclass j1 on j1.class_id = r1.reg_class_id where r1.reg_is_delete=0 AND r1.reg_state=0 AND r1.reg_payed=1
and j1.class_year='2014' and j1.class_season_name="秋季班" and j1.class_profit_name='中高级英语事业部-自营' and j1.class_business_type=0
)qq on qq.sid = reg.reg_student_id
where jrc.class_year = "2014"
AND (jrc.class_season_name="春季班" or jrc.class_season_name="暑假班")
and jrc.class_profit_name='少儿英语事业部-自营'
and jrc.class_name like '%剑桥英语3级下册%'
and jrc.class_business_type=0
AND reg.reg_is_delete=0 AND reg.reg_state=0 AND reg.reg_payed=1
group by reg.reg_class_id
limit 2

