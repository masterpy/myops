SELECT
shop.card_shop_school AS '售出分校',
shop.card_purchaser AS '购买人',
shop.card_purchaser_tel AS '购买人电话',
shop.card_num AS '爱学卡卡号',
shop.card_money AS '面值',
shop.card_contract_code AS '合同号',
shop.card_increase AS '爱心卡赠送金额',
shop.recommend_name AS '推荐人',
jrcard.num AS '爱心卡卡号',
shop.card_shop_time AS '售卡日期'
FROM
`tb_juren_shopcardinfos` AS shop
LEFT JOIN `tb_juren_cards` AS cards
ON shop.card_num = cards.jc_card_num
LEFT JOIN `jr_cards` AS jrcard
ON shop.card_num = jrcard.use_card_num
WHERE cards.jc_card_type = '8'
AND shop.card_shop_time >= '2014-07-28 00:00:00'
AND shop.card_shop_time <= '2014-08-04 00:00:00'
