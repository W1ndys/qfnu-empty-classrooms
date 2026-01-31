package auth

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"math/big"
)

const (
	aesChars    = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
	aesCharsLen = len(aesChars)
)

// EncryptPassword 使用 QFNU CAS 特定的 AES/CBC/PKCS7 算法加密密码
// password: 明文密码
// salt: 从登录页面获取的动态盐
func EncryptPassword(password, salt string) (string, error) {
	// 1. 生成64位随机前缀和16位随机IV
	prefix, err := randomString(64)
	if err != nil {
		return "", fmt.Errorf("生成随机前缀失败: %w", err)
	}
	iv, err := randomString(16)
	if err != nil {
		return "", fmt.Errorf("生成随机IV失败: %w", err)
	}

	// 2. 组合数据
	dataToEncrypt := []byte(prefix + password)
	key := []byte(salt)
	ivBytes := []byte(iv)

	// 3. 创建 AES 加密器
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("创建 AES Cipher 失败: %w", err)
	}

	// 4. PKCS7 填充
	paddedData := pkcs7Pad(dataToEncrypt, aes.BlockSize)

	// 5. CBC 模式加密
	mode := cipher.NewCBCEncrypter(block, ivBytes)
	encryptedData := make([]byte, len(paddedData))
	mode.CryptBlocks(encryptedData, paddedData)

	// 6. Base64 编码
	return base64.StdEncoding.EncodeToString(encryptedData), nil
}

// randomString 生成指定长度的随机字符串
func randomString(length int) (string, error) {
	b := make([]byte, length)
	for i := range b {
		n, err := rand.Int(rand.Reader, big.NewInt(int64(aesCharsLen)))
		if err != nil {
			return "", err
		}
		b[i] = aesChars[n.Int64()]
	}
	return string(b), nil
}

// pkcs7Pad 对数据进行 PKCS7 填充
func pkcs7Pad(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	padText := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(data, padText...)
}
