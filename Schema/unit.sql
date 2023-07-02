CREATE TABLE `unit` (
  `unit_id` int(11) NOT NULL AUTO_INCREMENT,
  `unit_name` varchar(100) NOT NULL,
  `unit_type` varchar(100) NOT NULL,
  `unit_era` varchar(50) NOT NULL,
  `unit_persona` int(11) DEFAULT NULL,
  PRIMARY KEY (`unit_id`)
);