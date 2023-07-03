CREATE TABLE `primary_unit_attributes` (
  `unit_id` int(11) NOT NULL,
  `force_points` tinyint(4) NOT NULL,
  `squad_points` tinyint(4) NOT NULL,
  UNIQUE KEY `unit_id` (`unit_id`)
);
