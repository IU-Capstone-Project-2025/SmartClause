package com.capstone.SmartClause.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class Controller {
    @GetMapping
    public ResponseEntity<String> index() {
        return ResponseEntity.ok("Welcome to SmartClause!");
    }
}
