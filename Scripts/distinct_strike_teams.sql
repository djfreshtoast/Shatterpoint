SET @include_unreleased := 1;

CREATE TEMPORARY TABLE IF NOT EXISTS tempUnits
SELECT u.unit_id, 
	   u.unit_type, 
       u.unit_persona, 
       oua.points_cost, 
       ug.unit_group_released,
       u.unit_era
FROM unit u
INNER JOIN other_unit_attributes oua ON oua.unit_id = u.unit_id
INNER JOIN unit_group_assignment uga ON uga.unit_id = u.unit_id
INNER JOIN unit_group ug ON ug.unit_group_id = uga.unit_group_id;

WITH primaryPairCte as (SELECT prim_a.unit_id as a_uid, prim_b.unit_id as b_uid
FROM unit prim_a
CROSS JOIN unit prim_b
INNER JOIN unit_group_assignment ugaA ON ugaA.unit_id = prim_a.unit_id
INNER JOIN unit_group_assignment ugaB on ugaB.unit_id = prim_b.unit_id
LEFT JOIN unit_group ugA ON ugA.unit_group_id = ugaA.unit_group_id
LEFT JOIN unit_group ugB ON ugB.unit_group_id = ugaB.unit_group_id
WHERE prim_a.unit_id != prim_b.unit_id
AND (ugA.unit_group_released = 1 OR @include_unreleased = 1)
AND (ugB.unit_group_released = 1 OR @include_unreleased = 1)
AND ifnull(prim_a.unit_persona, -1) != ifnull(prim_b.unit_persona, -2)
AND prim_a.unit_type = 'Primary' and prim_b.unit_type = 'Primary'),
distinctPrimaries AS
(SELECT DISTINCT CASE WHEN a_uid < b_uid THEN a_uid ELSE b_uid END as lowest,
	   CASE WHEN a_uid < b_uid THEN b_uid ELSE a_uid END as highest
FROM primaryPairCte),
finalPrimaries as (
SELECT priA.unit_id as priA_unitId,
	   priA.unit_persona as priA_persona,
	   puaA.squad_points as priA_squadPoints,
       priA.unit_era as priA_era,
       priB.unit_id as priB_unitId,
       priB.unit_persona as priB_persona,
       puaB.squad_points as priB_squadPoints,
       priB.unit_era as priB_era
FROM distinctPrimaries dp
INNER JOIN unit priA ON priA.unit_id = dp.lowest
INNER JOIN unit priB ON priB.unit_id = dp.highest
LEFT JOIN primary_unit_attributes puaA ON puaA.unit_id = priA.unit_id
LEFT JOIN primary_unit_attributes puaB on puaB.unit_id = priB.unit_id),
withFirstSecondary AS (
SELECT fp.*, 
	   sec.unit_id as secA_unitId,
	   sec.unit_persona as secA_persona,
       sec.unit_era as secA_era,
       tu.points_cost as secA_pointsCost
FROM finalPrimaries fp
CROSS JOIN unit sec
INNER JOIN tempUnits tu ON tu.unit_id = sec.unit_id
WHERE sec.unit_type = 'Secondary' 
AND ifnull(sec.unit_persona, -1) NOT IN (ifnull(fp.priA_persona, -2), ifnull(fp.priB_persona, -2))
AND (tu.unit_group_released = 1 OR @include_unreleased = 1)),
squadOneDone as
(
SELECT wfs.*,
	   sup.unit_id as supA_unitId,
       sup.unit_persona as supA_persona,
       tu.points_cost as supA_pointsCost,
       sup.unit_era as supA_era
FROM withFirstSecondary wfs
CROSS JOIN unit sup
INNER JOIN tempUnits tu ON tu.unit_id = sup.unit_id
WHERE sup.unit_type = 'Supporting' 
AND ifnull(sup.unit_persona, -1) NOT IN (ifnull(wfs.priA_persona, -2), ifnull(wfs.priB_persona, -2), ifnull(wfs.secA_persona, -2))
AND (tu.unit_group_released = 1 OR @include_unreleased = 1)
AND wfs.secA_pointsCost + tu.points_cost <= wfs.priA_squadPoints),
secondSecondDone AS (
SELECT sod.*,
	   secB.unit_id as secB_unitId,
       secB.unit_persona as secB_persona,
       tu.points_cost as secB_pointsCost,
       secB.unit_era as secB_era
FROM squadOneDone sod
CROSS JOIN unit secB
INNER JOIN tempUnits tu ON tu.unit_id = secB.unit_id
WHERE secB.unit_type = 'Secondary' AND ifnull(secB.unit_persona, -1) NOT IN (ifnull(sod.priA_persona, -2), ifnull(sod.priB_persona, -2), ifnull(sod.secA_persona, -2), ifnull(sod.supA_persona, -2))
AND (tu.unit_group_released = 1 OR @include_unreleased = 1) AND secB.unit_id != sod.secA_unitId)

SELECT ssd.*,
	   supB.unit_id as supB_unitId,
       supB.unit_persona as supB_persona,
       supB.unit_era as supB_era
FROM secondSecondDone ssd
CROSS JOIN unit supB
INNER JOIN tempUnits tu ON tu.unit_id = supB.unit_id
WHERE supB.unit_type = 'Supporting'
AND ifnull(supB.unit_persona, -1) NOT IN (ifnull(ssd.priA_persona, -2), ifnull(ssd.priB_persona, -2), ifnull(ssd.secA_persona, -2), ifnull(ssd.supA_persona, -2), ifnull(ssd.secB_persona, -2))
AND (tu.unit_group_released = 1 OR @include_unreleased = 1) AND supB.unit_id != ssd.supA_unitId
AND tu.points_cost + ssd.secB_pointsCost <= priB_squadPoints