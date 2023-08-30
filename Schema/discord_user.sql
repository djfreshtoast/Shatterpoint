CREATE TABLE `discord_user` (
  `user_id` varchar(255) NOT NULL,
  `user_name` varchar(255) NOT NULL,
  `user_display_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
)
