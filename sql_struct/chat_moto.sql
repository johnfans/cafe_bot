/*
 Navicat MySQL Dump SQL

 Source Server         : msq
 Source Server Type    : MySQL
 Source Server Version : 80042 (8.0.42)
 Source Host           : localhost:3306
 Source Schema         : wx_record

 Target Server Type    : MySQL
 Target Server Version : 80042 (8.0.42)
 File Encoding         : 65001

 Date: 08/03/2026 20:08:53
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for chat_moto
-- ----------------------------
DROP TABLE IF EXISTS `chat_moto`;
CREATE TABLE `chat_moto`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `start` bigint NOT NULL,
  `end` bigint NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_zh_0900_as_cs ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
