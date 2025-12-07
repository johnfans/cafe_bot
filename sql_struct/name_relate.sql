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

 Date: 07/12/2025 15:26:39
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for name_relate
-- ----------------------------
DROP TABLE IF EXISTS `name_relate`;
CREATE TABLE `name_relate`  (
  `atname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_zh_0900_as_cs NOT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_zh_0900_as_cs NULL DEFAULT NULL,
  PRIMARY KEY (`atname`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_zh_0900_as_cs ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
