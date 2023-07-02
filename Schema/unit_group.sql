CREATE TABLE `unit_group` (
  `unit_group_id` varchar(100) NOT NULL,
  `unit_group_name` varchar(255) NOT NULL,
  `unit_group_released` bit(1) NOT NULL DEFAULT b'1',
  PRIMARY KEY (`unit_group_id`)
);